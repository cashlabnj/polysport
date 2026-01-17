from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Dict


@dataclass(frozen=True)
class OddsSnapshot:
    market_id: str
    outcomes: Dict[str, float]
    captured_at: datetime


class OddsProvider(ABC):
    @abstractmethod
    def fetch(self) -> list[OddsSnapshot]:
        raise NotImplementedError
