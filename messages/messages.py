import json

from abc import ABC, abstractmethod
from typing import Any

from loguru import logger as log


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
        # log.debug(f'Incoming {data=}')
        # log.debug(f"SER::message_is_valid: {data.get("type") == "stateEvents"}")
        return data.get("type") == "stateEvents"

    @classmethod
    def _unwrap_response(cls, data: str | dict[str, Any]) -> Any:
        d = super()._unwrap_response(data)
        if isinstance(d, str):
            d = json.loads(d)

        return d["payload"]


class SubscribeStateEventsRequest(StateEventsRequest):
    def _get_request_payload(self, _=None) -> dict[str, Any]:
        return super()._get_request_payload(
            {"event": "listen", "token": "gg_kekemui_veadosc"}
        )


class UnsubscribeStateEventsRequest(StateEventsRequest):
    def _get_request_payload(self, _=None) -> dict[str, Any]:
        return super()._get_request_payload(
            {"event": "unlisten", "token": "gg_kekemui_veadosc"}
        )


class ListStateEventsRequest(StateEventsRequest):
    def _get_request_payload(self, _=None) -> dict[str, Any]:
        return super()._get_request_payload({"event": "list"})


class ListStateEventsResponse(StateEventsResponse):
    @classmethod
    def message_is_valid(cls, data: dict[str, Any]) -> bool:
        if not super().message_is_valid(data):
            return False

        unwrapped = super()._unwrap_response(data)
        # log.debug(f'{unwrapped}')
        # log.debug(f'Is valid List? {unwrapped.get("event") == "list"}')
        return unwrapped.get("event") == "list"

    def __init__(self, payload):
        unwrapped = super()._unwrap_response(payload)
        self.states = unwrapped["states"]


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


class SetActiveStateRequest(StateEventsRequest):
    def __init__(self, state_id: str):
        self.state_id = state_id

    def _get_request_payload(self, _=None) -> dict[str, Any]:
        return super()._get_request_payload({"event": "set", "state": self.state_id})


NODES_RESPONSE_TYPES: list[StateEventsResponse] = [
    ListStateEventsResponse,
    PeekResponse,
    ThumbnailResponse,
]


def response_factory(message: str) -> StateEventsResponse:
    data = json.loads(Response._unwrap_response(message))
    # (x for x in event.states if x["state_id"] == self.state_id)
    clazz = next((x for x in NODES_RESPONSE_TYPES if x.message_is_valid(data)), None)
    # log.debug(f'Detected message type: {clazz}')
    if clazz:
        return clazz(data)
