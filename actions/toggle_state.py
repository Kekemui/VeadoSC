from loguru import logger as log  # noqa: F401

from gg_kekemui_veadosc.messages import ToggleStateRequest
from gg_kekemui_veadosc.utils import constants
from .action_bases import StateActionBase


class ToggleState(StateActionBase):

    action_id = f"{constants.REV_DNS}::ToggleState"
    action_name = "Toggle State"

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
