# Import StreamController modules
from src.backend.PluginManager.ActionBase import ActionBase
from src.backend.DeckManagement.DeckController import DeckController  # noqa
from src.backend.PageManagement.Page import Page  # noqa
from src.backend.PluginManager.PluginBase import PluginBase  # noqa

from dataclasses import dataclass
from loguru import logger as log
from uuid import uuid4
from PIL import ImageFile
from ..messages import (
    StateEventsResponse,
    ListStateEventsRequest,
    ListStateEventsResponse,
    SetActiveStateRequest,
    PeekRequest,
    PeekResponse,
    ThumbnailRequest,
    ThumbnailResponse,
)
from ..utils import get_image_from_b64

# Import gtk modules - used for the config rows
import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw  # noqa: E402, F401


@dataclass
class ActionState:
    state_id: str | None = None
    is_active: bool = False
    image_hash: str | None = None
    image: ImageFile.ImageFile | None = None


BG_ACTIVE = [111, 202, 28, 255]
BG_INACTIVE = [68, 100, 38, 255]
BG_UNKNOWN = [0, 0, 0, 255]


class SetState(ActionBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.subscriber_id = str(uuid4())
        self.vsc_state = None
        self.plugin_base.subscribe(self.subscriber_id, self.callback)

    def on_key_down(self):
        if not self.vsc_state.image_hash:
            log.warning(
                "Received keypress to set Veado state, but our own state is incomplete. Ignoring."
            )
            return
        self.plugin_base.send_request(SetActiveStateRequest(self.vsc_state.state_id))
        # self.plugin_base.send_request(PeekRequest())

    def callback(self, event: StateEventsResponse):
        if self.vsc_state is None:
            self.vsc_state = ActionState(state_id=self.get_settings().get("state_id"))

        log.debug(f"Action received {event=}")
        if isinstance(event, ListStateEventsResponse):
            log.debug(f"Our {self.vsc_state.state_id=}")
            log.debug(f"Incoming state IDs: {list(x['id'] for x in event.states)}")
            our_state = next(
                (x for x in event.states if x["id"] == self.vsc_state.state_id), None
            )
            if not our_state:
                return

            log.debug(f"{self.vsc_state.image_hash=} ?= {our_state['thumbHash']=}")
            if our_state["thumbHash"] != self.vsc_state.image_hash:
                self.plugin_base.send_request(ThumbnailRequest(self.vsc_state.state_id))
        elif isinstance(event, PeekResponse):
            new_is_active = event.current_state == self.vsc_state.state_id
            if self.vsc_state.is_active != new_is_active:
                self.vsc_state.is_active = new_is_active
                self.render()
        elif isinstance(event, ThumbnailResponse):
            if event.state_id != self.vsc_state.state_id:
                return
            self.vsc_state.image_hash = event.hash
            self.vsc_state.image = get_image_from_b64(event.png_b64_str)
            self.render()

    def on_ready(self):
        self.vsc_state = ActionState(state_id=self.get_settings().get("state_id"))
        self.plugin_base.send_request(ListStateEventsRequest())
        self.plugin_base.send_request(PeekRequest())
        self.render(force=True)

    def render(self, force: bool = False):

        if not self.on_ready_called and not force:
            return

        self.set_bottom_label(self.vsc_state.state_id, update=False)

        if self.vsc_state.image:
            self.set_media(image=self.vsc_state.image, size=0.75, update=False)

        log.debug(f"{self.vsc_state.state_id}: {self.vsc_state.is_active=}")
        match self.vsc_state.is_active:
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

        # TODO - Reconnect backend

    def on_port_update(self, spinner, *args):
        settings = self.plugin_base.get_settings()
        settings["port"] = int(spinner.get_value())
        self.plugin_base.set_settings(settings)

        # TODO - Reconnect backend

    def on_state_id_update(self, entry, *args):
        log.debug("on_state_id_update")
        new_state_id = entry.get_text().strip()

        settings = self.get_settings()
        settings["state_id"] = new_state_id
        self.set_settings(settings)

        if self.vsc_state.state_id != new_state_id:
            # Clear state, list all states
            self.vsc_state = ActionState(state_id=new_state_id)
            self.plugin_base.send_request(ListStateEventsRequest())
