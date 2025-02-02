from collections import defaultdict
from loguru import logger as log

from ..messages import (
    ListStateEventsRequest,
    ListStateEventsResponse,
    PeekRequest,
    PeekResponse,
    StateEventsResponse,
    ThumbnailRequest,
    ThumbnailResponse,
)
from ..utils import Observer, Subject, get_image_from_b64
from ..veado_controller import ControllerConnectedEvent, VeadoController
from .types import VeadoState


class VeadoModel(Subject, Observer):
    def __init__(self, controller: VeadoController):
        super().__init__()
        self.states: dict[str, VeadoState] = defaultdict(lambda: VeadoState())
        self.active_state: str = ""

        self.controller: VeadoController = controller

        self.update_map = {
            ListStateEventsResponse: self._list_update,
            PeekResponse: self._peek_update,
            ThumbnailResponse: self._thumb_update,
            ControllerConnectedEvent: self._connected_update,
        }

        self.controller.subscribe(self)
        self.connected: bool = controller.is_connected()
        self.bootstrap()

    def update(self, event: StateEventsResponse):
        update_impl = self.update_map.get(type(event), self._default_update)
        update_impl(event)
        self.notify()

    def bootstrap(self):
        self.controller.send_request(ListStateEventsRequest())
        self.controller.send_request(PeekRequest())

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
        log.warn(
            f"Received unknown StateEventsResponse type {type(event)}: {event.__repr__()}"
        )
