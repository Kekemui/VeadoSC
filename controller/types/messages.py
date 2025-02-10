import json

from abc import ABC, abstractmethod
from typing import Any

from loguru import logger as log  # noqa: F401

import gg_kekemui_veadosc.model.events as me


class VeadoBase(ABC):
    @classmethod
    @abstractmethod
    def get_channel(cls) -> str:
        pass


class NodesBase(VeadoBase):
    @classmethod
    def get_channel(cls):
        return "nodes"


class Request(ABC):
    @abstractmethod
    def _get_request_payload(self, incoming: dict | None = None) -> dict[str, Any]:
        pass

    def to_request_string(self) -> str:
        return f"{self.get_channel()}:{json.dumps(self._get_request_payload())}"


class Response(ABC):
    @classmethod
    def _unwrap_response(cls, data: str | dict[str, Any]) -> Any:
        if isinstance(data, str):
            return data.split(":", maxsplit=1)[1]
        else:
            return data

    @classmethod
    @abstractmethod
    def message_is_valid(cls, data: dict[str, Any]) -> bool:
        pass


class StateEventsRequest(NodesBase, Request, ABC):

    def _get_request_payload(self, incoming: dict[str, Any]) -> dict[str, Any]:
        return {
            "event": "payload",
            "type": "stateEvents",
            "id": "mini",
            "name": "avatar state",
            "payload": incoming,
        }


class StateEventsResponse(NodesBase, Response, ABC):

    @classmethod
    def message_is_valid(cls, data: dict[str, Any]) -> bool:
        return data.get("type") == "stateEvents"

    @classmethod
    def _unwrap_response(cls, data: str | dict[str, Any]) -> Any:
        d = super()._unwrap_response(data)
        if isinstance(d, str):
            d = json.loads(d)

        return d["payload"]

    @abstractmethod
    def to_model_event(self) -> me.ModelEvent:
        raise NotImplementedError()


class SubscribeStateEventsRequest(StateEventsRequest):
    def _get_request_payload(self, _=None) -> dict[str, Any]:
        return super()._get_request_payload({"event": "listen", "token": "gg_kekemui_veadosc"})


class UnsubscribeStateEventsRequest(StateEventsRequest):
    def _get_request_payload(self, _=None) -> dict[str, Any]:
        return super()._get_request_payload({"event": "unlisten", "token": "gg_kekemui_veadosc"})


class ListStateEventsRequest(StateEventsRequest):
    def _get_request_payload(self, _=None) -> dict[str, Any]:
        return super()._get_request_payload({"event": "list"})


class StateDetail:
    def __init__(self, state: dict[str, str]):
        self.state_id = state["id"]
        self.state_name = state["name"]
        self.thumb_hash = state["thumbHash"]


class ListStateEventsResponse(StateEventsResponse):
    @classmethod
    def message_is_valid(cls, data: dict[str, Any]) -> bool:
        if not super().message_is_valid(data):
            return False

        unwrapped = super()._unwrap_response(data)
        return unwrapped.get("event") == "list"

    def __init__(self, payload):
        unwrapped = super()._unwrap_response(payload)
        self.states = unwrapped["states"]
        self.state_details: list[StateDetail] = []
        for state in unwrapped["states"]:
            self.state_details.append(StateDetail(state))

    def to_model_event(self) -> me.AllStatesEvent:
        return me.AllStatesEvent(states=self.state_details)


class PeekRequest(StateEventsRequest):
    def _get_request_payload(self, _=None) -> dict[str, Any]:
        return super()._get_request_payload({"event": "peek"})


class PeekResponse(StateEventsResponse):
    @classmethod
    def message_is_valid(cls, data: dict[str, Any]) -> bool:
        if not super().message_is_valid(data):
            return False

        unwrapped = super()._unwrap_response(data)
        return unwrapped.get("event") == "peek"

    def __init__(self, payload):
        unwrapped = super()._unwrap_response(payload)
        self.current_state = unwrapped["state"]

    def to_model_event(self) -> me.ActiveStateEvent:
        return me.ActiveStateEvent(state_id=self.current_state)


class ThumbnailRequest(StateEventsRequest):
    def __init__(self, state_id: str):
        self.state_id = state_id

    def _get_request_payload(self, _=None) -> dict[str, Any]:
        return super()._get_request_payload({"event": "thumb", "state": self.state_id})


class ThumbnailResponse(StateEventsResponse):
    @classmethod
    def message_is_valid(cls, data: dict[str, Any]) -> bool:
        if not super().message_is_valid(data):
            return False

        unwrapped = super()._unwrap_response(data)
        return unwrapped.get("event") == "thumb"

    def __init__(self, payload):
        unwrapped = super()._unwrap_response(payload)
        self.state_id = unwrapped["state"]
        self.hash = unwrapped["hash"]
        self.width = unwrapped["width"]
        self.height = unwrapped["height"]
        self.png_b64_str = unwrapped["png"]

    def to_model_event(self) -> me.ThumbnailEvent:
        return me.ThumbnailEvent(state_id=self.state_id, thumb_hash=self.hash, thumb_b64_str=self.png_b64_str)


class SetActiveStateRequest(StateEventsRequest):
    def __init__(self, state_id: str):
        self.state_id = state_id

    def _get_request_payload(self, _=None) -> dict[str, Any]:
        return super()._get_request_payload({"event": "set", "state": self.state_id})


class ToggleStateRequest(StateEventsRequest):
    def __init__(self, state_id: str):
        self.state_id = state_id

    def _get_request_payload(self, _=None) -> dict[str, Any]:
        return super()._get_request_payload({"event": "toggle", "state": self.state_id})


NODES_RESPONSE_TYPES: list[StateEventsResponse] = [
    ListStateEventsResponse,
    PeekResponse,
    ThumbnailResponse,
]


def model_event_factory(message: str) -> me.ModelEvent:
    data = json.loads(Response._unwrap_response(message))
    clazz = next((x for x in NODES_RESPONSE_TYPES if x.message_is_valid(data)), None)
    if clazz:
        return clazz(data).to_model_event()
    else:
        log.debug(f"Received unknown message {message}")
