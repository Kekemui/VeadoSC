import os
from collections import defaultdict

from loguru import logger as log
from PIL.ImageFile import ImageFile

from gg_kekemui_veadosc.controller.types import (
    ControllerConnectedEvent,
    ListStateEventsRequest,
    PeekRequest,
    ThumbnailRequest,
    VeadoController,
)
from gg_kekemui_veadosc.model import (
    ActiveStateEvent,
    AllStatesEvent,
    ThumbnailEvent,
    VeadoState,
)
from gg_kekemui_veadosc.model.abc import VeadoModel
from gg_kekemui_veadosc.model.utils import get_image_from_b64, get_image_from_path
from gg_kekemui_veadosc.observer import Event

BG_ACTIVE = [111, 202, 28, 255]
BG_INACTIVE = [68, 100, 38, 255]
BG_ERROR = [71, 0, 14, 255]


class VeadoModel_(VeadoModel):
    def __init__(self, frontend, controller: VeadoController, base_path: str):
        super().__init__()
        self.states: dict[str, VeadoState] = defaultdict(lambda: VeadoState())
        self.active_state: str = ""

        self.controller: VeadoController = controller

        self.disconnected_image = get_image_from_path(os.path.join(base_path, "assets", "ix-icons", "disconnected.png"))
        self.not_found_image = get_image_from_path(os.path.join(base_path, "assets", "ix-icons", "missing-symbol.png"))

        self.update_map = {
            AllStatesEvent: self._list_update,
            ActiveStateEvent: self._peek_update,
            ThumbnailEvent: self._thumb_update,
            ControllerConnectedEvent: self._connected_update,
        }

        # Use the frontend's proxied events
        frontend.subscribe(self)
        self.connected: bool = controller.connected
        self.bootstrap()

    def update(self, event: Event):
        update_impl = self._default_update
        for event_type, handler in self.update_map.items():
            if isinstance(event, event_type):
                update_impl = handler
                break

        update_impl(event)
        self.notify(event)

    @property
    def state_list(self) -> list[str]:
        return list(self.states.keys())

    def bootstrap(self):
        self.controller.send_request(ListStateEventsRequest())
        self.controller.send_request(PeekRequest())

    def get_color_for_state(self, state_id: str) -> list[int]:
        if not self.connected or state_id not in self.states:
            return BG_ERROR
        elif state_id == self.active_state:
            return BG_ACTIVE
        else:
            return BG_INACTIVE

    def get_image_for_state(self, state_id: str) -> ImageFile:
        if not self.connected:
            return self.disconnected_image

        state = self.states.get(state_id)
        if state and state.thumbnail:
            return state.thumbnail
        else:
            return self.not_found_image

    def _list_update(self, event: AllStatesEvent):
        current_keys = set(self.states.keys())
        for state in event.states:
            if state.state_id in current_keys:
                current_keys.remove(state.state_id)
            vstate: VeadoState = self.states[state.state_id]
            vstate.state_id = state.state_id
            vstate.state_name = state.state_name

            if vstate.thumb_hash != state.thumb_hash:
                vstate.thumbnail = None
                vstate.thumb_hash = state.thumb_hash
                self.controller.send_request(ThumbnailRequest(vstate.state_id))

        for key in current_keys:  # Clean up deleted items
            del self.states[key]

    def _peek_update(self, event: ActiveStateEvent):
        for state in self.states.values():
            state.is_active = False

        self.states[event.state_id].is_active = True
        self.active_state = event.state_id

    def _thumb_update(self, event: ThumbnailEvent):
        state = self.states[event.state_id]
        state.state_id = event.state_id
        state.thumb_hash = event.thumb_hash
        state.thumbnail = get_image_from_b64(event.thumb_b64_str)

    def _connected_update(self, event: ControllerConnectedEvent):
        self.connected = event.is_connected
        if self.connected:
            self.bootstrap()

    def _default_update(self, event: Event):
        log.warning(f"Received unknown Event type {event.event_name}: {event.__repr__()}")
