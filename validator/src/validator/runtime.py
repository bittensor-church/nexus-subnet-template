from __future__ import annotations

from nexus.v1 import NexusValidator

from validator.settings import Settings


class Validator(NexusValidator):
    def __init__(self, settings: Settings) -> None:
        super().__init__(settings)
