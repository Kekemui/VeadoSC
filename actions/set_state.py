from loguru import logger as log  # noqa: F401

from ..messages import (
    SetActiveStateRequest,
)
from .action_bases import StateActionBase
from ..utils import constants


class SetState(StateActionBase):

    action_id = f"{constants.REV_DNS}::SetState"
    action_name = "Set State"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def on_key_down(self):
        success = self.plugin_base.send_request(SetActiveStateRequest(self.state_id))

        if not success:
            self.show_error(5)
