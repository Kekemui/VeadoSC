from loguru import logger as log  # noqa: F401

from src.backend.PluginManager.EventAssigner import EventAssigner
from src.backend.DeckManagement.InputIdentifier import Input, InputEvent

from gg_kekemui_veadosc.actions.action_bases import StateActionBase
from gg_kekemui_veadosc.constants import REV_DNS
from gg_kekemui_veadosc.controller.types import ToggleStateRequest


class ToggleState(StateActionBase):

    action_id = f"{REV_DNS}::ToggleState"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.add_event_assigner(EventAssigner(
            id="Temp Enable State",
            ui_label="Temporarily Enable State",
            default_event=Input.Key.Events.DOWN,
            callback=lambda _: self.toggle()
        ))

        self.add_event_assigner(EventAssigner(
            id="Revert to Prev State",
            ui_label="Revert to Previous State",
            default_event=Input.Key.Events.UP,
            callback=lambda _: self.toggle()
        ))

    def toggle(self):
        success = self.plugin_base.send_request(ToggleStateRequest(self.state_id))

        if not success:
            self.show_error(5)

    def render(self):
        self.set_top_label("Toggle", update=False)
        super().render()
