from __future__ import annotations

from nexus.nexus_validator import NexusValidator

from validator.settings import Settings


class Validator(NexusValidator):
    def __init__(self, settings: Settings) -> None:
        super().__init__(settings)
