from loguru import logger as log  # noqa: F401

from gg_kekemui_veadosc.constants import REV_DNS
from gg_kekemui_veadosc.controller.types import SetActiveStateRequest

from gg_kekemui_veadosc.actions.action_bases import StateActionBase


class SetState(StateActionBase):

    action_id = f"{REV_DNS}::SetState"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def on_key_down(self):
        success = self.plugin_base.send_request(SetActiveStateRequest(self.state_id))

        if not success:
            self.show_error(5)
