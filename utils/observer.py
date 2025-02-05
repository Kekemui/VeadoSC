from abc import ABC, abstractmethod
from uuid import uuid4

from loguru import logger as log


class Observer(ABC):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.observer_id = str(uuid4())

    def get_observer_id(self):
        try:
            return self.observer_id
        except AttributeError:
            return None

    @abstractmethod
    def update(self, *args, **kwargs):
        pass


class Subject(ABC):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.observers: dict[str, callable] = {}

    def subscribe(self, observer: Observer):
        oid = observer.get_observer_id()
        if oid is None:
            log.error(
                f"{observer=} does not have an observer_id. {observer.__repr__()}"
            )
        self.observers[oid] = observer

    def unsubscribe(self, observer: Observer):
        del self.observers[observer.get_observer_id()]

    def notify(self, *args, **kwargs):
        for observer in list(self.observers.values()):
            try:
                observer.update(*args, **kwargs)
            except Exception as e:
                log.warning(
                    f"Caught exception {e=} while dispatching updates. Continuing."
                )
