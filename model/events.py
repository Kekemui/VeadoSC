from abc import ABC, abstractmethod
from dataclasses import dataclass

from gg_kekemui_veadosc.model.types import StateDetail
from gg_kekemui_veadosc.observer import Event

BASE_EVENT_NAME = "model."

class ModelEvent(Event, ABC):
    pass

@dataclass
class ThumbnailEvent(ModelEvent):
    state_id: str
    thumb_hash: str
    thumb_b64_str: str

    event_name = BASE_EVENT_NAME + "ThumbnailEvent"


@dataclass
class ActiveStateEvent(ModelEvent):
    state_id: str

    event_name = BASE_EVENT_NAME + "ActiveStateEvent"


@dataclass
class AllStatesEvent(ModelEvent):
    states: list[StateDetail]

    event_name = BASE_EVENT_NAME + "AllStatesEvent"
