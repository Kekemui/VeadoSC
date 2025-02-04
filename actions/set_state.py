from loguru import logger as log  # noqa: F401

from ..messages import (
    SetActiveStateRequest,
)
from .action_bases import StateActionBase

# Import gtk modules - used for the config rows
import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw  # noqa: E402, F401


class SetState(StateActionBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def on_key_down(self):
        success = self.plugin_base.send_request(SetActiveStateRequest(self.state_id))

        if not success:
            self.show_error(5)
