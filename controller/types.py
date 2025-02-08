from abc import ABC, abstractmethod
from dataclasses import dataclass, asdict
from json import dumps, loads
from pathlib import Path


@dataclass
class VTInstance:
    veado_id: str
    hostname: str
    port: int

    def to_json_string(self):
        return dumps(asdict(self))

    @classmethod
    def from_json_string(cls, value: str) -> "VTInstance":
        d = loads(value)
        return VTInstance(**d)

    @classmethod
    def from_path(cls, path: Path) -> "VTInstance":
        contents = path.read_text()
        info = loads(contents)
        try:
            veado_id = info["id"]
            host_port = info["server"]
        except KeyError:
            return None
        host_parts = host_port.split(":")
        return VTInstance(veado_id=veado_id, hostname=host_parts[0], port=host_parts[1])


class ConnectionManager(ABC):

    def __init__(self):
        super().__init__()

    @abstractmethod
    def terminate_connection(self, instance: VTInstance):
        pass

    @abstractmethod
    def propose_connection(self, instance: VTInstance):
        pass
