from dataclasses import dataclass
import threading

from loguru import logger as log

from websockets.exceptions import InvalidURI, InvalidHandshake, ConnectionClosed
from websockets.sync import client

from gg_kekemui_veadosc.data import VeadoSCConnectionConfig
from gg_kekemui_veadosc.messages import (
    Request,
    response_factory,
    SubscribeStateEventsRequest,
)
from gg_kekemui_veadosc.utils import Subject

from gg_kekemui_veadosc.controller.types import VTInstance


@dataclass
class ControllerConnectedEvent:
    is_connected: bool


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
        log.warning("Connection terminated by request")


class VeadoController(Subject):
    def __init__(self, plugin_base):
        super().__init__()
        self.frontend = plugin_base
        self._config: VeadoSCConnectionConfig = None

        self._conn: VTConnection = None

    @property
    def config(self) -> VeadoSCConnectionConfig:
        return self._config

    @config.setter
    def config(self, value):
        if self._config == value:
            return

        self._config = value
        self._restart()

    @property
    def connected(self) -> bool:
        return bool(self._conn and self._conn.connected)

    def _restart(self):
        if self._conn:
            self.terminate_connection(force=True)

        if not self.config.smart_connect:
            instance = VTInstance(
                veado_id="", hostname=self.config.hostname, port=self.config.port
            )
            self.propose_connection(instance)

    def propose_connection(self, instance: VTInstance):
        if self._conn:
            log.warning(
                f"Received request to connect to {instance}, but already talking to {self._conn.conf}"
            )
            return

        log.info(f"Accepting proposal to connect to {instance}")
        self._conn = VTConnection(self, instance)

    def terminate_connection(
        self, instance: VTInstance | None = None, force: bool = False
    ):
        if not self._conn:
            log.info("Nothing to terminate")
            return

        if not force and instance != self._conn.conf:
            log.info(
                f"Received request to terminate {instance}, but connected to {self._conn.conf}"
            )
            return

        log.warning(f"Terminating {self._conn.conf}")
        self._conn.terminate()
        self._conn = None

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
