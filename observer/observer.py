from abc import ABC, abstractmethod
from uuid import uuid4
import traceback

from loguru import logger as log

from .event import Event


class Observer(ABC):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.observer_id = str(uuid4())

    @abstractmethod
    def update(self, event: Event):
        pass


class Subject(ABC):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.observers: dict[str, callable] = {}

    def subscribe(self, observer: Observer):
        if hasattr(observer, "observer_id"):
            self.observers[observer.observer_id] = observer.update
        else:
            log.error(f"{observer=} does not have an observer_id. {observer.__repr__()}")

    def unsubscribe(self, observer: Observer):
        try:
            del self.observers[observer.observer_id]
        except KeyError:
            pass

    def notify(self, event: Event):
        for observer in list(self.observers.values()):
            try:
                # TODO - Should we do an instance-wide threadpool here?
                observer(event)
            except Exception as e:
                log.warning(f"Caught exception {e=} while dispatching updates. Full details: {traceback.format_exc()}")
