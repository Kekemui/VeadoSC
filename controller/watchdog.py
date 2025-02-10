from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from queue import SimpleQueue, Empty
import threading

from loguru import logger as log

from gg_kekemui_veadosc.controller.types import VTInstance
from .types.abc import ConnectionManager


@dataclass
class FileData:
    contents: VTInstance
    modified: int


class EventType(Enum):
    MODIFIED = 1
    DELETED = 2


@dataclass
class FileEvent:
    event: EventType
    new_instance: VTInstance | None = None
    old_instance: VTInstance | None = None


FS_POLL_TIME = 2.5
FS_THREAD_NAME = "gg_kekemui_veadosc::vpw_fs_poller"

QUEUE_THREAD_NAME = "gg_kekemui_veadosc::queue_poller"
QUEUE_WAIT_TIME = 5


class VeadoPollingWatchdog:
    def __init__(self, cm: ConnectionManager):
        self._cm = cm

        self._update_queue = SimpleQueue()

        self._queue_thread = threading.Thread(target=self._queue_consumer, name=QUEUE_THREAD_NAME, daemon=True)
        self._queue_thread.start()

        self._fs_thread: threading.Thread = None
        self._watch_dir: Path = None
        self._stop_fs_thread = threading.Event()
        self._files: dict[str, FileData] = {}

    def start_poller(self, watch_dir: Path):
        if not watch_dir:
            log.warning("VeadoPollingWatchdog::start_poller called with None watch_dir")
            return

        dir_str = str(watch_dir)
        if not dir_str.endswith("instances") and not dir_str.endswith("instances/"):
            log.warning(f"Watchdog configured with path {dir_str} that does not end with `instances`. Ignoring.")
            return

        self.stop_poller()

        self._stop_fs_thread.clear()
        self._watch_dir = watch_dir
        self._fs_thread = threading.Thread(target=self._fs_poller, name=FS_THREAD_NAME, daemon=True)
        self._fs_thread.start()

    def stop_poller(self):
        if not self._stop_fs_thread:
            return

        self._stop_fs_thread.set()
        self._files = {}
        self._watch_dir = None

    def _fs_poller(self):
        log.info(f"FS Poller started, monitoring {str(self._watch_dir.absolute())}")

        should_continue = True
        while should_continue:
            try:
                updated_files: dict[str, FileData] = {}
                for f in self._watch_dir.iterdir():
                    instance = VTInstance.from_path(f)
                    if not instance:
                        continue

                    mod_time = int(f.lstat().st_mtime)
                    updated_files[str(f.absolute())] = FileData(instance, mod_time)

                for path, file_data in updated_files.items():
                    if path not in self._files:  # net-new
                        self._update_queue.put(FileEvent(EventType.MODIFIED, file_data.contents))
                    else:
                        if file_data.contents != self._files[path].contents:
                            self._update_queue.put(
                                FileEvent(
                                    EventType.MODIFIED,
                                    file_data.contents,
                                    self._files[path].contents,
                                )
                            )
                        del self._files[path]

                for path, file_data in self._files.items():  # Anything left over was deleted
                    self._update_queue.put(FileEvent(EventType.DELETED, old_instance=file_data.contents))

                self._files = updated_files
            except FileNotFoundError as e:
                log.warning(f"Couldn't find {e.filename}. Suppressing exception.")

            should_continue = not self._stop_fs_thread.wait(timeout=FS_POLL_TIME)
        log.info("FS thread terminating")

    def _queue_consumer(self):
        log.info("Queue consumer started")
        while True:
            try:
                event = self._update_queue.get(block=True, timeout=QUEUE_WAIT_TIME)

                if event.old_instance:
                    self._cm.terminate_connection(event.old_instance)

                if event.new_instance:
                    self._cm.propose_connection(event.new_instance)

            except Empty:
                continue
