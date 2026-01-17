from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class IdempotencyStore:
    keys: set[str] = field(default_factory=set)

    def seen(self, key: str) -> bool:
        return key in self.keys

    def add(self, key: str) -> None:
        self.keys.add(key)
