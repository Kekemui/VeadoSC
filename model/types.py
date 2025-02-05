from dataclasses import dataclass
from json import dumps, loads
from pathlib import Path
from typing import Any

from loguru import logger as log
from PIL.ImageFile import ImageFile


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
    thumbnail: ImageFile | None = None
    is_active: bool = False
