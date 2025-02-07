from pathlib import Path
import sys

ABSOLUTE_PLUGIN_PATH = str(Path(__file__).parent.parent.parent.absolute())
sys.path.insert(0, ABSOLUTE_PLUGIN_PATH)

from streamcontroller_plugin_tools import BackendBase

from gg_kekemui_veadosc.controller.fswatch import VeadoWatchdog


class Backend(BackendBase):
    def __init__(self):
        super().__init__()

        self.watchdog = VeadoWatchdog(self)

    def create_watchdog(self, path: str):
        self.watchdog.create_watchdog(path)

    def terminate_watchdog(self):
        self.watchdog.terminate_watchdog()


backend = Backend()
