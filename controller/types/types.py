from dataclasses import asdict, dataclass
from json import dumps, loads
from pathlib import Path

from gg_kekemui_veadosc.observer import Event


@dataclass
class ControllerConnectedEvent(Event):
    is_connected: bool

    @property
    def event_name(self):
        return "observer.ControllerConnectedEvent"


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
