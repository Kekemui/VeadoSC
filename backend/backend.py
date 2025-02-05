from pathlib import Path
import sys

ABSOLUTE_PLUGIN_PATH = str(Path(__file__).parent.parent.parent.absolute())
sys.path.insert(0, ABSOLUTE_PLUGIN_PATH)

from streamcontroller_plugin_tools import BackendBase

from gg_kekemui_veadosc.controller import VeadoController

class Backend(BackendBase):
    def __init__(self):
        super().__init__()

        self.ctrl = VeadoController(self.frontend)

    def get_controller(self):
        return self.ctrl

backend = Backend()