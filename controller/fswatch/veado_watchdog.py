import json
from pathlib import Path
from typing import Any

from loguru import logger as log
from watchdog.observers import Observer
from watchdog.events import (
    FileSystemEventHandler,
    FileCreatedEvent,
    FileModifiedEvent,
    FileDeletedEvent,
)

from gg_kekemui_veadosc.controller.types import VTInstance


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

    def __init__(self, watchdog: "VeadoWatchdog"):
        self.known_instances: dict[str, VTInstance] = {}
        self.watchdog = watchdog

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

        if old_instance:
            self.watchdog.terminate_connection(old_instance)

        self.watchdog.propose_connection(new_instance)

    def on_deleted(self, event: FileDeletedEvent | Any):
        if not isinstance(event, FileDeletedEvent):
            return

        veado_id = Path(event.src_path).name

        if veado_id not in self.known_instances:
            log.warning(
                f"File {veado_id} deleted, but not in known set {self.known_instances.keys()}"
            )

        outgoing_instance = self.known_instances[veado_id]
        self.watchdog.terminate_connection(outgoing_instance)
        del self.known_instances[veado_id]
        # As is, if there's another instance in the folder that is actively
        # listening, we won't connect. Not sure if we should.


class VeadoWatchdog:

    def __init__(self, backend):
        self._watchdog_handler = VeadoWatchdogHandler(self)
        self.backend = backend
        self._watchdog = None

    def terminate_watchdog(self):
        if self._watchdog:
            self._watchdog.stop()
            self._watchdog.join()
            self._watchdog_handler.clear()
            self._watchdog = None
            log.info("Terminated fs watch")

    def create_watchdog(self, path: str):

        self.terminate_watchdog()

        log.info("Starting fs watch")

        # Improvement - list the directory before we kick off the watchdog.
        # Watchdog will pick up running veadotube instances - assuming vt
        # continues to rewrite the instance file every few seconds. If that
        # changes, we're sunk.
        observer = Observer()
        watch_dir = str(Path(path).expanduser())
        observer.schedule(
            self._watchdog_handler,
            watch_dir,
            recursive=True,
            event_filter=[FileCreatedEvent, FileDeletedEvent, FileModifiedEvent],
        )
        observer.start()
        self._watchdog = observer
        log.info(f"Monitoring {watch_dir}")

    def propose_connection(self, instance: VTInstance):
        i = instance.to_json_string()
        log.trace(f"propose_connection: {i}")
        self.backend.frontend.propose_connection(i)

    def terminate_connection(self, instance: VTInstance):
        i = instance.to_json_string()
        log.trace(f"terminate_connection: {i}")
        self.backend.frontend.terminate_connection(i)
