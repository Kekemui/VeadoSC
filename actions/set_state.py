# Import StreamController modules
from src.backend.PluginManager.ActionBase import ActionBase
from src.backend.DeckManagement.DeckController import DeckController  # noqa
from src.backend.PageManagement.Page import Page  # noqa
from src.backend.PluginManager.PluginBase import PluginBase  # noqa

from loguru import logger as log
from ..messages import (
    SetActiveStateRequest,
)
from ..model import VeadoState
from ..utils import Observer

# Import gtk modules - used for the config rows
import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw  # noqa: E402, F401


BG_ACTIVE = [111, 202, 28, 255]
BG_INACTIVE = [68, 100, 38, 255]
BG_UNKNOWN = [71, 0, 14, 255]


class SetState(Observer, ActionBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def on_key_down(self):
        self.plugin_base.send_request(SetActiveStateRequest(self.state_id))

    def update(self):
        self.render()

    def on_ready(self):
        self.plugin_base.model.subscribe(self)
        self.state_id = self.get_settings().get("state_id")
        self.render(force=True)

    def on_remove(self):
        self.plugin_base.model.unsubscribe(self)

    def render(self, force: bool = False):
        if not self.on_ready_called and not force:
            return

        state: VeadoState = self.plugin_base.model.states.get(self.state_id)

        if state is None:
            self.set_bottom_label(self.state_id, update=False)
            self.set_media(image=None, update=False)
            self.set_background_color(BG_UNKNOWN)
        else:
            self.set_bottom_label(state.state_id, update=False)

            if state.thumbnail:
                self.set_media(image=state.thumbnail, size=0.75, update=False)

            match state.is_active:
                case True:
                    self.set_background_color(BG_ACTIVE, update=False)
                case False:
                    self.set_background_color(BG_INACTIVE, update=False)
                case None:
                    self.set_background_color(BG_UNKNOWN, update=False)

        self.get_input().update()

    def get_config_rows(self):
        self.ip_entry = Adw.EntryRow(title="Veadotube IP Address")
        self.port_spinner = Adw.SpinRow.new_with_range(0, 65535, 1)
        self.port_spinner.set_title("Veadotube Static Port")
        self.state_id_entry = Adw.EntryRow(title="State Name")

        self.load_config_defaults()

        self.ip_entry.connect("notify::text", self.on_ip_update)
        self.port_spinner.connect("notify::value", self.on_port_update)
        self.state_id_entry.connect("notify::text", self.on_state_id_update)
        return [self.ip_entry, self.port_spinner, self.state_id_entry]

    def load_config_defaults(self):
        global_settings = self.plugin_base.get_settings()
        ip = global_settings.setdefault("ip", "localhost")
        port = global_settings.setdefault("port", 40404)

        local_settings = self.get_settings()
        state_id = local_settings.setdefault("state_id", "")

        self.ip_entry.set_text(ip)
        self.port_spinner.set_value(port)
        self.state_id_entry.set_text(state_id)

    def on_ip_update(self, entry, *args):
        settings = self.plugin_base.get_settings()
        settings["ip"] = entry.get_text().strip()
        self.plugin_base.set_settings(settings)

    def on_port_update(self, spinner, *args):
        settings = self.plugin_base.get_settings()
        settings["port"] = int(spinner.get_value())
        self.plugin_base.set_settings(settings)

    def on_state_id_update(self, entry, *args):
        log.debug("on_state_id_update")
        new_state_id = entry.get_text().strip()

        settings = self.get_settings()
        settings["state_id"] = new_state_id
        self.set_settings(settings)

        if self.state_id != new_state_id:
            self.state_id = new_state_id
            self.render()
