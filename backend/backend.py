# Set path so we can use absolute import paths
import sys
from pathlib import Path

ABSOLUTE_PLUGIN_PATH = str(Path(__file__).parent.parent.parent.absolute())
sys.path.insert(0, ABSOLUTE_PLUGIN_PATH)

from streamcontroller_plugin_tools import BackendBase

from gg_kekemui_veadosc.controller.impl import VeadoController_


class Backend(BackendBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.controller = VeadoController_(self.frontend)

    def get_controller(self):
        return self.controller


backend = Backend()
