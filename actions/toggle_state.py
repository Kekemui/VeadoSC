from loguru import logger as log  # noqa: F401

from gg_kekemui_veadosc.constants import REV_DNS
from gg_kekemui_veadosc.controller.types import ToggleStateRequest

from gg_kekemui_veadosc.actions.action_bases import StateActionBase


class ToggleState(StateActionBase):

    action_id = f"{REV_DNS}::ToggleState"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def on_key_down(self):
        self.toggle()

    def on_key_up(self):
        self.toggle()

    def toggle(self):
        success = self.plugin_base.send_request(ToggleStateRequest(self.state_id))

        if not success:
            self.show_error(5)

    def render(self):
        self.set_top_label("Toggle", update=False)
        super().render()
