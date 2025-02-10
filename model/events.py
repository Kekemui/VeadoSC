from abc import ABC, abstractmethod
from dataclasses import dataclass

from gg_kekemui_veadosc.model.types import StateDetail
from gg_kekemui_veadosc.observer import Event


class ModelEvent(Event, ABC):
    @property
    @abstractmethod
    def event_name(self):
        return "model."


@dataclass
class ThumbnailEvent(ModelEvent):
    state_id: str
    thumb_hash: str
    thumb_b64_str: str

    @property
    def event_name(self):
        return super().event_name() + "ThumbnailEvent"


@dataclass
class ActiveStateEvent(ModelEvent):
    state_id: str

    @property
    def event_name(self):
        return super().event_name() + "ActiveStateEvent"


@dataclass
class AllStatesEvent(ModelEvent):
    states: list[StateDetail]

    @property
    def event_name(self):
        return super().event_name() + "AllStatesEvent"
