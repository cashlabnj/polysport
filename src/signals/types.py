from __future__ import annotations

from dataclasses import dataclass, field
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


@dataclass
class OutcomeSnapshot:
    """Snapshot of an outcome's current state."""

    outcome_id: str
    name: str
    current_price: float
    price_history: list[float] = field(default_factory=list)


@dataclass
class MarketSnapshot:
    """Snapshot of a market for strategy evaluation."""

    market_id: str
    question: str
    outcomes: list[OutcomeSnapshot]
    close_time: datetime | None = None
    volume_24h: float = 0.0
    last_updated: datetime | None = None
