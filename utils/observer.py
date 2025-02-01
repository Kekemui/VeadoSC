from abc import ABC, abstractmethod
from typing import Any
from uuid import uuid4

from loguru import logger as log


class Observer(ABC):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        log.debug("Observer init")
        self.observer_id = str(uuid4())

    @abstractmethod
    def update(self, event: Any):
        pass


class Subject(ABC):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        log.debug("Subject init")
        self.observers: dict[str, callable] = {}

    def subscribe(self, observer: Observer):
        if not hasattr(observer, "observer_id"):
            log.error(
                f"{observer=} does not have an observer_id. {observer.__repr__()}"
            )
        self.observers[observer.observer_id] = observer.update

    def unsubscribe(self, observer: Observer):
        del self.observers[observer.observer_id]

    def notify(self, *args, **kwargs):
        for observer in list(self.observers.values()):
            try:
                observer(*args, **kwargs)
            except Exception as e:
                log.warn(
                    f"Caught exception {e=} while dispatching updates. Continuing."
                )
