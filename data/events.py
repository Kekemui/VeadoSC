from dataclasses import dataclass

@dataclass
class ControllerConnectedEvent:
    is_connected: bool