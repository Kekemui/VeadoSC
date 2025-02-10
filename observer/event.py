from abc import ABC, abstractmethod


class Event(ABC):

    @property
    @abstractmethod
    def event_name(self) -> str:
        return ""
