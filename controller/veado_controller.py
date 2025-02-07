from dataclasses import dataclass
import json
from pathlib import Path
import threading
from typing import Any

from loguru import logger as log
from watchdog.observers import Observer
from watchdog.events import (
    FileSystemEvent,
    FileSystemEventHandler,
    FileCreatedEvent,
    FileModifiedEvent,
    FileDeletedEvent,
)
from websockets.exceptions import InvalidURI, InvalidHandshake, ConnectionClosed
from websockets.sync import client

from gg_kekemui_veadosc.data import ControllerConnectedEvent, VeadoSCConnectionConfig
from gg_kekemui_veadosc.messages import (
    Request,
    response_factory,
    SubscribeStateEventsRequest,
)
from gg_kekemui_veadosc.utils import Subject


@dataclass
class VTInstance:
    veado_id: str
    hostname: str
    port: int


def info_from_path(raw_path: str) -> (str, VTInstance):
    path = Path(raw_path)
    contents = path.read_text()
    info = json.loads(contents)
    try:
        veado_id = info["id"]
        host_port = info["server"]
    except KeyError:
        return None
    host_parts = host_port.split(":")
    return VTInstance(veado_id=veado_id, hostname=host_parts[0], port=host_parts[1])


class VeadoWatchdogHandler(FileSystemEventHandler):

    def __init__(self, controller: "VeadoController"):
        self.known_instances: dict[str, VTInstance] = {}
        self.ctrl = controller

    def clear(self):
        self.known_instances = {}

    # on_created and on_modified were basically doing the same thing, but the
    # watchdog was so fast that we were hitting a race condition. We now just
    # rely on on_modified to do the work of both.
    def on_modified(self, event: FileModifiedEvent | Any):
        if not isinstance(event, FileModifiedEvent):
            return

        new_instance = info_from_path(event.src_path)

        if not new_instance:
            return

        if new_instance == self.known_instances.get(new_instance.veado_id):
            # No changes, nothing to do here
            return

        old_instance = self.known_instances.get(new_instance.veado_id)
        self.known_instances[new_instance.veado_id] = new_instance
        log.warning(f"Detected change to instance {new_instance.veado_id}")
        self.ctrl._terminate_connection(old_instance)
        self.ctrl._propose_connection(new_instance)

    def on_deleted(self, event: FileDeletedEvent | Any):
        if not isinstance(event, FileDeletedEvent):
            return

        veado_id = Path(event.src_path).name

        if veado_id not in self.known_instances:
            log.warning(
                f"File {veado_id} deleted, but not in known set {self.known_instances.keys()}"
            )

        outgoing_instance = self.known_instances[veado_id]
        self.ctrl._terminate_connection(outgoing_instance)
        del self.known_instances[veado_id]
        # As is, if there's another instance in the folder that is actively
        # listening, we won't connect. Not sure if we should.


class VTConnection:
    def __init__(self, controller: "VeadoController", conf: VTInstance):
        self.ctrl = controller
        self.conf = conf

        self.should_terminate = threading.Event()
        self.ws = None

        self.start_ws_thread()

    @property
    def connected(self) -> bool:
        return self.ws is not None

    def terminate(self):
        self.should_terminate.set()
        if self.ws:
            self.ws.close()

    def send_request(self, request: Request) -> bool:
        """
        Sends a request to veadotube, if connected.

        :param request: The request to send.

        :returns: True if successful, False if not successful (e.g., if not connected
            to a veadotube instance). It may be more Pythonic to ask
            forgiveness than to seek permission, but in most cases we don't
            want to explode callers if we're not connected.
        """
        try:
            reqstr = request.to_request_string()
            self.ws.send(reqstr)
            return True
        except AttributeError:
            return False

    def start_ws_thread(self):
        self.should_terminate.clear()
        self.thread = threading.Thread(
            target=self.ws_thread, name="gg_kekemui_veadosc_wst", daemon=True
        )
        self.thread.start()

    def ws_thread(self):
        should_terminate: bool = self.should_terminate.is_set()
        while not should_terminate:
            host = self.conf.hostname
            port = self.conf.port
            try:
                self.ws: client.ClientConnection = client.connect(
                    f"ws://{host}:{port}?n=gg_kekemui_veadosc"
                )

                self.send_request(SubscribeStateEventsRequest())

                self.ctrl.notify(ControllerConnectedEvent(True))

                for message in self.ws:
                    self.ctrl.on_recv(message)
            except (InvalidURI, InvalidHandshake, OSError, TimeoutError):
                log.info("Unable to connect")
            except ConnectionClosed:
                log.info("Websocket closed")

            if self.ws:
                self.ws = None
                self.ctrl.notify(ControllerConnectedEvent(False))
            should_terminate = self.should_terminate.wait(10)
        log.warning(f"Connection terminated by request")


class VeadoController(Subject):
    def __init__(self, plugin_base):
        super().__init__()
        self.frontend = plugin_base
        self._config: VeadoSCConnectionConfig = None

        self._conn: VTConnection = None
        self._watchdog: Observer = None
        self._watchdog_handler = VeadoWatchdogHandler(self)

    @property
    def config(self) -> VeadoSCConnectionConfig:
        return self._config

    @config.setter
    def config(self, value):
        if self._config == value:
            return

        self._config = value
        self._restart()

    def set_config(self, value):
        if isinstance(value, str):
            value = VeadoSCConnectionConfig.from_json_string(value)
        self.config = value

    @property
    def connected(self) -> bool:
        return self._conn and self._conn.connected

    def _restart(self):
        if self._conn:
            self._terminate_connection(force=True)

        if self._watchdog:
            self._watchdog.stop()
            self._watchdog.join()
            self._watchdog_handler.clear()
            self._watchdog = None

        if self.config.smart_connect:
            self._create_watchdog()
        else:
            instance = VTInstance(
                veado_id="", hostname=self.config.hostname, port=self.config.port
            )
            self._propose_connection(instance)

    def _propose_connection(self, instance: VTInstance):
        if self._conn:
            log.warning(
                f"Received request to connect to {instance}, but already talking to {self._conn.conf}"
            )
            return

        log.info(f"Accepting proposal to connect to {instance}")
        self._conn = VTConnection(self, instance)

    def _terminate_connection(
        self, instance: VTInstance | None = None, force: bool = False
    ):
        if not self._conn:
            log.info(f"Nothing to terminate")
            return

        if not force and instance != self._conn.conf:
            log.info(
                f"Received request to terminate {instance}, but connected to {self._conn.conf}"
            )
            return

        log.warning(f"Terminating {self._conn.conf}")
        self._conn.terminate()
        self._conn = None

    def _create_watchdog(self):
        # Improvement - list the directory before we kick off the watchdog.
        # Watchdog will pick up running veadotube instances - assuming vt
        # continues to rewrite the instance file every few seconds. If that
        # changes, we're sunk.
        observer = Observer()
        watch_dir = str(self.config.instances_dir.expanduser())
        observer.schedule(
            self._watchdog_handler,
            watch_dir,
            recursive=True,
            event_filter=[FileCreatedEvent, FileDeletedEvent, FileModifiedEvent],
        )
        observer.start()
        self._watchdog = observer
        log.info(f"Monitoring {watch_dir}")

    def on_recv(self, message):
        event = response_factory(message)
        log.info(f"Received event {type(event)}")
        if event:
            self.notify(event=event)

    def send_request(self, request: Request) -> bool:
        """
        Sends a request to veadotube, if connected.

        :param request: The request to send.

        :returns: True if successful, False if not successful (e.g., if not connected
            to a veadotube instance). It may be more Pythonic to ask
            forgiveness than to seek permission, but in most cases we don't
            want to explode callers if we're not connected.
        """
        try:
            return self._conn.send_request(request)
        except AttributeError:
            return False
