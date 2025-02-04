from abc import ABC

from loguru import logger as log  # noqa: F401

from src.backend.PluginManager.ActionBase import ActionBase

from ..model import VeadoModel
from ..utils import Observer

# Import gtk modules - used for the config rows
import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw  # noqa: E402, F401


class VeadoGtk:

    def __init__(self, veado_ip: str, veado_port: int, is_connected: bool):
        self.expander = Adw.ExpanderRow(title="Veadotube Connection Config")
        self.ip_entry = Adw.EntryRow(title="Veadotube IP Address")
        self.port_spinner = Adw.SpinRow.new_with_range(0, 65535, 1)
        self.port_spinner.set_title("Veadotube Static Port")

        self.expander.add_row(self.ip_entry)
        self.expander.add_row(self.port_spinner)
        self.expander.set_expanded(not is_connected)

        self.ip_entry.set_text(veado_ip)
        self.port_spinner.set_value(veado_port)

    def get_config_rows(self) -> list[Adw.PreferencesRow]:
        return [self.expander]


class VeadoSCActionBase(Observer, ActionBase, ABC):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.model: VeadoModel = self.plugin_base.model

        self.veado_gtk: VeadoGtk | None = None

    def get_config_rows(self) -> list[Adw.PreferencesRow]:
        veado_gtk = VeadoGtk(
            veado_ip=self.plugin_base.veado_ip,
            veado_port=self.plugin_base.veado_port,
            is_connected=self.model.connected,
        )

        veado_gtk.ip_entry.connect("notify::text", self.on_gtk_ip_update)
        veado_gtk.port_spinner.connect("notify::value", self.on_gtk_port_update)

        self.veado_gtk = veado_gtk

        return self.veado_gtk.get_config_rows()

    # VeadoSC (plugin_base) handles restarting the controller on update here.
    def on_gtk_ip_update(self, entry, *args):
        self.plugin_base.veado_ip = entry.get_text().strip()

    def on_gtk_port_update(self, entry, *args):
        self.plugin_base.veado_port = int(entry.get_value())


class StateGtk:
    def __init__(self, action: "StateActionBase"):
        self.parent = action
        self.states_row = Adw.ComboRow(title="Available States")
        self.state_id_entry = Adw.EntryRow(title="State Name - Manual Entry")
        self.update_states()

    def get_config_rows(self):
        return [self.states_row, self.state_id_entry]

    def update_states(self):
        connected = self.parent.model.connected

        all_states: list[str] = []
        if connected:
            all_states += self.parent.model.state_list
        all_states.sort()
        all_states.append("(Other - enter below)")

        try:
            old_states = list(
                self.states_model[x].get_string()
                for x in range(0, self.states_model.get_n_items())
            )
        except AttributeError:
            old_states = []

        if all_states == old_states:
            # No changes since the last time we bootstrapped, carry on
            return

        self.disconnect_signals()

        self.states_model = Gtk.StringList()

        self.states_row.set_selected(Gtk.INVALID_LIST_POSITION)
        self.states_row.set_model(self.states_model)
        for state in all_states:
            self.states_model.append(state)

        state_id = self.parent.state_id
        if state_id in all_states:
            self.states_row.set_selected(all_states.index(state_id))
            self.state_id_entry.set_editable(False)
        else:
            self.states_row.set_selected(len(all_states) - 1)
            self.state_id_entry.set_text(state_id)

        self.connect_signals()

    def on_gtk_update(self, *args):
        self.disconnect_signals()

        selected_idx = self.states_row.get_selected()
        is_other_selected = selected_idx == self.states_model.get_n_items() - 1

        if is_other_selected:
            new_state_id = self.state_id_entry.get_text().strip()
        else:
            new_state_id = self.states_model[selected_idx].get_string()

        self.state_id_entry.set_editable(is_other_selected)
        self.parent.state_id = new_state_id

        self.connect_signals()

    def disconnect_signals(self):
        try:
            self.states_row.disconnect_by_func(self.on_gtk_update)
            self.state_id_entry.disconnect_by_func(self.on_gtk_update)
        except TypeError:
            pass

    def connect_signals(self):
        self.state_id_entry.connect("notify::text", self.on_gtk_update)
        self.states_row.connect("notify::selected", self.on_gtk_update)


class StateActionBase(VeadoSCActionBase, ABC):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @property
    def state_id(self) -> str:
        return self.get_settings().get("state_id", "")

    @state_id.setter
    def state_id(self, value):
        settings = self.get_settings()

        dirty = settings.get("state_id", "") != value
        settings["state_id"] = value
        self.set_settings(settings)

        if dirty:
            self.render()

    def render(self):
        if not self.on_ready_called:
            return

        self.set_media(
            image=self.model.get_image_for_state(self.state_id), size=0.75, update=False
        )
        self.set_background_color(
            self.model.get_color_for_state(self.state_id), update=False
        )
        self.set_bottom_label(self.state_id, update=False)

        self.get_input().update()

    def update(self):
        super().update()
        try:
            self.state_gtk.update_states()
        except AttributeError:
            pass

        self.render()

    def on_ready(self):
        self.model.subscribe(self)
        self.render()

    def on_remove(self):
        self.model.unsubscribe(self)

    def get_config_rows(self):
        self.state_gtk = StateGtk(self)
        return super().get_config_rows() + self.state_gtk.get_config_rows()
