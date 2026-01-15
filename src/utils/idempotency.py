from __future__ import annotations

from dataclasses import dataclass, field
from typing import Set


@dataclass
class IdempotencyStore:
    keys: Set[str] = field(default_factory=set)

    def seen(self, key: str) -> bool:
        return key in self.keys

    def add(self, key: str) -> None:
        self.keys.add(key)
