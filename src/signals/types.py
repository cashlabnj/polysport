from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class Signal:
    strategy: str
    market_id: str
    outcome_id: str
    action: str
    confidence: float
    explanation: dict[str, float | str]
    created_at: datetime


@dataclass(frozen=True)
class SignalBatch:
    signals: list[Signal]
    created_at: datetime
