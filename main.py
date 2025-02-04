# Import StreamController modules
from src.backend.PluginManager.PluginBase import PluginBase
from src.backend.PluginManager.ActionHolder import ActionHolder

# Import actions
from .actions import SetState
from .messages import Request, StateEventsResponse
from .model import VeadoModel
from .veado_controller import VeadoController

# import os
from loguru import logger as log

REV_DNS = "gg_kekemui_veadosc"


class VeadoSC(PluginBase):
    def __init__(self):
        super().__init__()

        # Internal data
        self.subscribers: dict[str, callable] = {}
        self.controller = VeadoController(self)

        self.model: VeadoModel = VeadoModel(self.controller, self.PATH)

        self.set_action_holder = ActionHolder(
            plugin_base=self,
            action_base=SetState,
            action_id=f"{REV_DNS}::SetState",
            action_name="Set State",
        )
        self.add_action_holder(self.set_action_holder)

        # Register plugin
        self.register(
            plugin_name="VeadoSC",
            github_repo="https://github.com/Kekemui/VeadoSC",
            plugin_version="0.0.1",
            app_version="1.5.0-beta.7",
        )

    def update_callback(self, event: StateEventsResponse):
        log.info(f"Received update: {event}")
        for c in self.subscribers.values():
            c(event)

    def send_request(self, request: Request) -> bool:
        return self.controller.send_request(request)

    @property
    def veado_ip(self) -> str:
        return self.get_settings().get("ip", "localhost")

    @veado_ip.setter
    def veado_ip(self, value: str):
        settings = self.get_settings()
        old_ip = self.veado_ip
        settings["ip"] = value
        self.set_settings(settings)

        if old_ip != value:  # dirty
            self.controller.restart()

    @property
    def veado_port(self) -> str:
        return self.get_settings().get("port", 40404)

    @veado_port.setter
    def veado_port(self, value: int):
        settings = self.get_settings()
        old_port = self.veado_port
        settings["port"] = value

        if old_port != value:
            self.controller.restart()

    def set_settings(self, settings: dict[str, str | int]):
        "Overrides base, triggers reconnect on changed configuration"
        old_settings = self.get_settings()
        dirty = settings != old_settings

        # Don't over-think this, let the base do its thing
        super().set_settings(settings)

        if dirty:
            self.controller.restart()
