from collections import defaultdict
import os

from loguru import logger as log
from PIL.ImageFile import ImageFile

from gg_kekemui_veadosc.data import ControllerConnectedEvent
from ..messages import (
    ListStateEventsRequest,
    ListStateEventsResponse,
    PeekRequest,
    PeekResponse,
    StateEventsResponse,
    ThumbnailRequest,
    ThumbnailResponse,
)
from gg_kekemui_veadosc.utils import (
    Observer,
    Subject,
    get_image_from_b64,
    get_image_from_path,
)

# from gg_kekemui_veadosc.controller import ControllerConnectedEvent, VeadoController
from .types import VeadoState

BG_ACTIVE = [111, 202, 28, 255]
BG_INACTIVE = [68, 100, 38, 255]
BG_ERROR = [71, 0, 14, 255]


class VeadoModel(Subject, Observer):
    def __init__(self, controller: "VeadoController", base_path: str):
        super().__init__()
        self.states: dict[str, VeadoState] = defaultdict(lambda: VeadoState())
        self.active_state: str = ""

        self.controller: "VeadoController" = controller

        self.disconnected_image = get_image_from_path(
            os.path.join(base_path, "assets", "ix-icons", "disconnected.png")
        )
        self.not_found_image = get_image_from_path(
            os.path.join(base_path, "assets", "ix-icons", "missing-symbol.png")
        )

        self.update_map = {
            ListStateEventsResponse: self._list_update,
            PeekResponse: self._peek_update,
            ThumbnailResponse: self._thumb_update,
            ControllerConnectedEvent: self._connected_update,
        }

        self.controller.subscribe(self)
        self.connected: bool = controller.connected
        self.bootstrap()

    def update(self, event: StateEventsResponse):
        update_impl = self.update_map.get(type(event), self._default_update)
        update_impl(event)
        self.notify()

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

    def _list_update(self, event: ListStateEventsResponse):
        current_keys = set(self.states.keys())
        for state in event.state_details:
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

    def _peek_update(self, event: PeekResponse):
        for state in self.states.values():
            state.is_active = False

        self.states[event.current_state].is_active = True
        self.active_state = event.current_state

    def _thumb_update(self, event: ThumbnailResponse):
        state = self.states[event.state_id]
        state.state_id = event.state_id
        state.thumb_hash = event.hash
        state.thumbnail = get_image_from_b64(event.png_b64_str)

    def _connected_update(self, event: ControllerConnectedEvent):
        self.connected = event.is_connected
        if self.connected:
            self.bootstrap()

    def _default_update(self, event: StateEventsResponse):
        log.warning(
            f"Received unknown StateEventsResponse type {type(event)}: {event.__repr__()}"
        )
