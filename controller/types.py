from dataclasses import dataclass, asdict
from json import dumps, loads


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
