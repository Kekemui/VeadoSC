import json
from pathlib import Path
from typing import Any

class VeadoSCConnectionConfig:

    SMART_CONNECT = 'smart_connect'
    INSTANCES_DIR = 'instances_dir'
    HOSTNAME = 'hostname'
    PORT = 'port'
    KEYS = (SMART_CONNECT, INSTANCES_DIR, HOSTNAME, PORT)

    def __init__(self, smart_connect: bool = True, instances_dir: Path | str = Path('~/.veadotube/instances'), hostname: str = 'localhost', port: int = 40404):
        self.smart_connect = smart_connect
        self.instances_dir = instances_dir if isinstance(instances_dir, Path) else Path(instances_dir)
        self.hostname = hostname
        self.port = port


    def to_dict(self) -> dict[str, Any]:
        d = {}
        d[self.SMART_CONNECT] = self.smart_connect
        d[self.INSTANCES_DIR] = str(self.instances_dir)
        d[self.HOSTNAME] = self.hostname
        d[self.PORT] = self.port

        return d

    def to_json_string(self) -> str:
        return json.dumps(self.to_dict())

    @classmethod
    def from_json_string(cls, json_str: str) -> 'VeadoSCConnectionConfig':
        return cls.from_dict(json.loads(json_str))

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> 'VeadoSCConnectionConfig':
        args = {k: v for k, v in d.items() if k in cls.KEYS and v is not None}
        
        if args.get(cls.INSTANCES_DIR):
            args[cls.INSTANCES_DIR] = Path(args[cls.INSTANCES_DIR])

        return VeadoSCConnectionConfig(**args)