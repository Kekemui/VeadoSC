from abc import ABC, abstractmethod

from gg_kekemui_veadosc.observer import Observer, Subject


class VeadoModel(Subject, Observer, ABC):

    @property
    @abstractmethod
    def state_list(self) -> list[str]:
        pass

    @abstractmethod
    def get_color_for_state(self, state_id: str) -> list[int]:
        pass

    @abstractmethod
    def get_image_for_state(self, state_id: str) -> "PIL.ImageFile.ImageFile":  # noqa: F821
        pass
