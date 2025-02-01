# Import StreamController modules
from src.backend.PluginManager.PluginBase import PluginBase
from src.backend.PluginManager.ActionHolder import ActionHolder

# Import actions
from .actions import SetState
from .messages import Request, StateEventsResponse
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
        self.controller.set_callback(self.update_callback)

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

    def send_request(self, request: Request):
        self.controller.send_request(request)

    def subscribe(self, callback_id: str, callback: callable):
        self.subscribers[callback_id] = callback

    def unsubscribe(self, callback_id: str):
        del self.subscribers[callback_id]
