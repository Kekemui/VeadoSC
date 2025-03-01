# Set path so we can use absolute import paths
import sys
from pathlib import Path

ABSOLUTE_PLUGIN_PATH = str(Path(__file__).parent.parent.absolute())
sys.path.insert(0, ABSOLUTE_PLUGIN_PATH)

import os

from loguru import logger as log  # noqa: F401
from src.backend.DeckManagement.InputIdentifier import Input
from src.backend.PluginManager.ActionHolder import ActionHolder
from src.backend.PluginManager.ActionInputSupport import ActionInputSupport

# Import StreamController modules
from src.backend.PluginManager.PluginBase import PluginBase

# Import actions
from gg_kekemui_veadosc.actions import SetState, ToggleState
from gg_kekemui_veadosc.controller.types import Request, VeadoController, VTInstance
from gg_kekemui_veadosc.data import VeadoSCConnectionConfig
from gg_kekemui_veadosc.model import VeadoModel
from gg_kekemui_veadosc.model.impl import VeadoModel_
from gg_kekemui_veadosc.observer import Event, Subject


DEBUG_ENV = "GG_KEKEMUI_VEADOSC_DEBUG"


class VeadoSC(Subject, PluginBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.lm = self.locale_manager

        debug_mode = DEBUG_ENV in os.environ

        backend_path = os.path.join(self.PATH, "backend", "backend.py")
        self.launch_backend(backend_path=backend_path, open_in_terminal=debug_mode)

        # The backend doesn't always launch within the 0.3 seconds afforded by
        # PluginBase. Give ourselves a bit more time.
        for i in range(10):
            if not self.backend_connection:
                self.wait_for_backend(10)
            else:
                break

        if not self.backend_connection:
            raise ValueError("Backend failed to launch after 10 seconds")

        self.controller: VeadoController = self.backend.get_controller()

        self.model: VeadoModel = VeadoModel_(self, self.controller, self.PATH)

        self._propagate_config(self.conn_conf, force=True)

        for action in [SetState, ToggleState]:
            self.add_action_holder(
                ActionHolder(
                    plugin_base=self,
                    action_base=action,
                    action_id=action.action_id,
                    action_name=self.locale_manager.get(action.action_id),
                    action_support={
                        Input.Key: ActionInputSupport.SUPPORTED,
                        Input.Dial: ActionInputSupport.UNTESTED,
                        Input.Touchscreen: ActionInputSupport.UNTESTED,
                    },
                )
            )

        # Register plugin
        self.register(
            plugin_name=self.lm.get("plugin.name"),
            github_repo="https://github.com/Kekemui/VeadoSC",
            plugin_version="1.0.0",
            app_version="1.5.0-beta.7",
        )

    def update(self, event: Event):
        """
        Provides proxying of events from the VeadoSC backend into this frontend.
        Should conform to the interface of `gg_kekemui_veadosc.observer.Observer`.

        See ADR-01 for why this exists.
        """
        self.notify(event)

    def send_request(self, request: Request) -> bool:
        return self.controller.send_request(request)

    def propose_connection(self, instance: VTInstance | str):
        if not isinstance(instance, VTInstance):
            instance = VTInstance.from_json_string(instance)

        self.controller.propose_connection(instance)

    def terminate_connection(self, instance: VTInstance | str):
        if not isinstance(instance, VTInstance):
            instance = VTInstance.from_json_string(instance)

        self.controller.terminate_connection(instance)

    @property
    def conn_conf(self) -> VeadoSCConnectionConfig:
        return VeadoSCConnectionConfig.from_dict(self.get_settings().get("connection", {}))

    @conn_conf.setter
    def conn_conf(self, value: VeadoSCConnectionConfig):
        old = self.conn_conf

        settings = self.get_settings()
        settings["connection"] = value.to_dict()
        self.set_settings(settings)

        if old != value:  # config is dirty
            self._propagate_config(value)

    def _propagate_config(self, value: VeadoSCConnectionConfig, force: bool = False):
        self.controller.set_config(value)
