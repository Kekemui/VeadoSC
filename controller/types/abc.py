from abc import ABC, abstractmethod

from gg_kekemui_veadosc.data import VeadoSCConnectionConfig

from .messages import Request
from .types import VTInstance


class ConnectionManager(ABC):

    def __init__(self):
        super().__init__()

    @abstractmethod
    def terminate_connection(self, instance: VTInstance):
        pass

    @abstractmethod
    def propose_connection(self, instance: VTInstance):
        pass


class VeadoController(ConnectionManager, ABC):

    @property
    @abstractmethod
    def config(self) -> VeadoSCConnectionConfig:
        pass

    @config.setter
    @abstractmethod
    def config(self, value: VeadoSCConnectionConfig):
        pass

    @property
    @abstractmethod
    def connected(self) -> bool:
        pass

    @abstractmethod
    def send_request(self, request: Request) -> bool:
        """
        Sends a request to veadotube, if connected.

        :param request: The request to send.

        :returns: True if successful, False if not successful (e.g., if not connected
            to a veadotube instance). It may be more Pythonic to ask
            forgiveness than to seek permission, but in most cases we don't
            want to explode callers if we're not connected.
        """
        pass
