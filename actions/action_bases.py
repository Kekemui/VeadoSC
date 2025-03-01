from abc import ABC
from pathlib import Path

# Import gtk modules - used for the config rows
import gi
from loguru import logger as log  # noqa: F401
from src.backend.PluginManager.ActionBase import ActionBase

from gg_kekemui_veadosc.data import VeadoSCConnectionConfig
from gg_kekemui_veadosc.model import ModelEvent, VeadoModel
from gg_kekemui_veadosc.observer import Observer

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gio, Gtk  # noqa: E402, F401


class VeadoGtk:

    def __init__(self, action: "VeadoSCActionBase", config: VeadoSCConnectionConfig, is_connected: bool, lm):
        self.action = action
        self.lm = lm

        self.expander = Adw.ExpanderRow(title=self.lm.get("actions.base.gtk.expando.title"))

        self.mode_switch = Adw.SwitchRow(
            title=self.lm.get("actions.base.gtk.mode_switch.title"),
            subtitle=self.lm.get("actions.base.gtk.mode_switch.subtitle"),
        )

        self.last_selected_dir = str(config.instances_dir.expanduser())

        self.instances_expando = Adw.ExpanderRow(title=self.lm.get("actions.base.gtk.smart_expando.title"))

        self.instances_path = Adw.ActionRow()
        self.instances_path.set_title(self.lm.get("actions.base.gtk.instance_path.title"))
        self.instances_path.add_css_class("property")

        b = Gtk.Button()
        b.set_icon_name("folder")
        b.add_css_class("suggested-action")
        self.instances_path.add_suffix(b)
        b.connect("clicked", self.launch_chooser)

        self.instances_expando.add_row(self.instances_path)

        self.direct_expando = Adw.ExpanderRow(title=self.lm.get("actions.base.gtk.direct_expando.title"))
        self.ip_entry = Adw.EntryRow(title=self.lm.get("actions.base.gtk.ip_entry.title"))
        self.port_spinner = Adw.SpinRow.new_with_range(0, 65535, 1)
        self.port_spinner.set_title(self.lm.get("actions.base.gtk.port_spinner.title"))

        self.direct_expando.add_row(self.ip_entry)
        self.direct_expando.add_row(self.port_spinner)

        self.expander.add_row(self.mode_switch)
        self.expander.add_row(self.instances_expando)
        self.expander.add_row(self.direct_expando)

        self.set_initial_values(config, is_connected)
        self.connect_signals()

    def launch_chooser(self, *args):
        dialog = Gtk.FileDialog(title=self.lm.get("actions.base.gtk.filedialog.title"), modal=True)
        dialog.set_initial_folder(Gio.File.parse_name(self.last_selected_dir))

        dialog.select_folder(parent=None, cancellable=None, callback=self.select_callback)

    def select_callback(self, dialog, result):
        try:
            selected_file = dialog.select_folder_finish(result)
            self.last_selected_dir = selected_file.get_path()
            self.on_gtk_update()
            log.error(f"{selected_file.get_path()}")
            log.error(f"{list(Path(self.last_selected_dir).iterdir())}")
        except gi.repository.GLib.GError:
            pass

    def get_config_rows(self) -> list[Adw.PreferencesRow]:
        return [self.expander]

    def set_initial_values(self, config: VeadoSCConnectionConfig, is_connected: bool):
        self.expander.set_expanded(not is_connected)

        self.mode_switch.set_active(config.smart_connect)

        self.ip_entry.set_text(config.hostname)
        self.port_spinner.set_value(config.port)

        self.update_gtk_model(config)

    def update_gtk_model(self, config: VeadoSCConnectionConfig):
        self.instances_expando.set_enable_expansion(config.smart_connect)
        self.instances_expando.set_expanded(config.smart_connect)

        self.instances_path.set_subtitle(self.last_selected_dir)

        self.direct_expando.set_expanded(not config.smart_connect)
        self.direct_expando.set_enable_expansion(not config.smart_connect)

    def connect_signals(self):
        self.mode_switch.connect("notify::active", self.on_gtk_update)
        self.ip_entry.connect("notify::text", self.on_gtk_update)
        self.port_spinner.connect("notify::value", self.on_gtk_update)

    def on_gtk_update(self, *args):
        should_use_smart = self.mode_switch.get_active()
        path = self.last_selected_dir
        hostname = self.ip_entry.get_text().strip()
        port = int(self.port_spinner.get_value())

        config = VeadoSCConnectionConfig(
            smart_connect=should_use_smart,
            instances_dir=path,
            hostname=hostname,
            port=port,
        )

        self.action.plugin_base.conn_conf = config
        self.update_gtk_model(config)


class VeadoSCActionBase(Observer, ActionBase, ABC):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.lm = self.plugin_base.locale_manager

        self.model: VeadoModel = self.plugin_base.model

        self.veado_gtk: VeadoGtk | None = None

    def get_config_rows(self) -> list[Adw.PreferencesRow]:
        veado_gtk = VeadoGtk(
            action=self, config=self.plugin_base.conn_conf, is_connected=self.model.connected, lm=self.lm
        )

        self.veado_gtk = veado_gtk

        return self.veado_gtk.get_config_rows()


class StateGtk:
    def __init__(self, action: "StateActionBase", lm):
        self.parent = action
        self.lm = lm

        self.state_id_entry = Adw.EntryRow(title=self.lm.get("actions.state.gtk.state_id_entry.title"))
        self.update_states()

    def get_config_rows(self):
        return [self.state_id_entry]

    def update_states(self):
        self.state_id_entry.set_text(self.parent.state_id)
        self.connect_signals()

    def on_gtk_update(self, *args):
        self.parent.state_id = self.state_id_entry.get_text().strip()

    def disconnect_signals(self):
        try:
            self.state_id_entry.disconnect_by_func(self.on_gtk_update)
        except TypeError:
            pass

    def connect_signals(self):
        self.state_id_entry.connect("notify::text", self.on_gtk_update)


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

        self.set_media(image=self.model.get_image_for_state(self.state_id), size=0.75, update=False)
        self.set_background_color(self.model.get_color_for_state(self.state_id), update=False)
        self.set_bottom_label(self.state_id, update=False)

        self.get_input().update()

    def update(self, event: ModelEvent):
        super().update(event)

        self.render()

    def on_ready(self):
        self.model.subscribe(self)
        self.render()

    def on_remove(self):
        self.model.unsubscribe(self)

    def get_config_rows(self):
        self.state_gtk = StateGtk(self, self.lm)
        return super().get_config_rows() + self.state_gtk.get_config_rows()
