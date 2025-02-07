# Set path so we can use absolute import paths
from pathlib import Path
import sys

ABSOLUTE_PLUGIN_PATH = str(Path(__file__).parent.parent.absolute())
sys.path.insert(0, ABSOLUTE_PLUGIN_PATH)

import os

# Import StreamController modules
from src.backend.PluginManager.PluginBase import PluginBase
from src.backend.PluginManager.ActionHolder import ActionHolder

# Import actions
from gg_kekemui_veadosc.actions import SetState, ToggleState

# from gg_kekemui_veadosc.controller import VeadoController
from gg_kekemui_veadosc.data import VeadoSCConnectionConfig
from gg_kekemui_veadosc.messages import Request
from gg_kekemui_veadosc.model import VeadoModel

from loguru import logger as log  # noqa: F401

from time import sleep


class VeadoSC(PluginBase):
    def __init__(self):
        super().__init__()

        backend_path = os.path.join(self.PATH, "backend", "backend.py")
        backend_venv = os.path.join(self.PATH, "backend", ".venv")
        self.launch_backend(
            backend_path=backend_path, venv_path=backend_venv, open_in_terminal=True
        )

        sleep(5)

        self.controller = self.backend.get_controller()
        self.controller.set_config(self.conn_conf.to_json_string())

        self.model: VeadoModel = VeadoModel(self.controller, self.PATH)

        for base in [SetState, ToggleState]:
            self.add_action_holder(
                ActionHolder(
                    plugin_base=self,
                    action_base=base,
                    action_id=base.action_id,
                    action_name=base.action_name,
                )
            )

        # Register plugin
        self.register(
            plugin_name="VeadoSC",
            github_repo="https://github.com/Kekemui/VeadoSC",
            plugin_version="0.0.1",
            app_version="1.5.0-beta.7",
        )

    def send_request(self, request: Request) -> bool:
        return self.controller.send_request(request)

    @property
    def conn_conf(self) -> VeadoSCConnectionConfig:
        return VeadoSCConnectionConfig.from_dict(
            self.get_settings().get("connection", {})
        )

    @conn_conf.setter
    def conn_conf(self, value: VeadoSCConnectionConfig):
        old = self.conn_conf  # This might blow up spectacularly

        settings = self.get_settings()
        settings["connection"] = value.to_dict()
        self.set_settings(settings)

        if old != value:  # dirty
            self.controller.set_config(value)
