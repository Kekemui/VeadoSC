from dataclasses import dataclass
from typing import Optional


class StateDetail:
    def __init__(self, state: dict[str, str]):
        self.state_id = state["id"]
        self.state_name = state["name"]
        self.thumb_hash = state["thumbHash"]


@dataclass
class VeadoState:
    """
    This represents a comprehensive model of a Veadotube `state`'s members.
    Under the covers, this represents a union of the data served from `list`,
    `peek`, and `thumb` requests.
    """

    state_id: str | None = None
    state_name: str | None = None
    thumb_hash: str | None = None
    thumbnail: Optional["PIL.ImageFile.ImageFile"] = None  # noqa: F821
    is_active: bool = False
