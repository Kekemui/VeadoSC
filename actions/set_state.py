from loguru import logger as log  # noqa: F401

from src.backend.PluginManager.EventAssigner import EventAssigner
from src.backend.DeckManagement.InputIdentifier import Input, InputEvent

from gg_kekemui_veadosc.actions.action_bases import StateActionBase
from gg_kekemui_veadosc.constants import REV_DNS
from gg_kekemui_veadosc.controller.types import SetActiveStateRequest


class SetState(StateActionBase):

    action_id = f"{REV_DNS}::SetState"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.add_event_assigner(EventAssigner(
            id="Switch to State",
            ui_label="Switch to State",
            default_event=Input.Key.Events.DOWN,
            callback=lambda _: self.set_veado_state()
        ))

    def set_veado_state(self):
        success = self.plugin_base.send_request(SetActiveStateRequest(self.state_id))

        if not success:
            self.show_error(5)
