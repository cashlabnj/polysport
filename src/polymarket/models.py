from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime


def _utc_now() -> datetime:
    """Return current UTC time (for dataclass default factory)."""
    return datetime.now(UTC)


@dataclass(frozen=True)
class Outcome:
    id: str
    name: str
    price: float


@dataclass(frozen=True)
class Market:
    id: str
    question: str
    outcomes: Sequence[Outcome]
    active: bool
    close_time: datetime | None = None


@dataclass(frozen=True)
class Order:
    id: str
    market_id: str
    outcome_id: str
    side: str
    price: float
    size: float
    status: str
    created_at: datetime = field(default_factory=_utc_now)


@dataclass(frozen=True)
class Fill:
    id: str
    order_id: str
    market_id: str
    outcome_id: str
    price: float
    size: float
    timestamp: datetime


@dataclass(frozen=True)
class Position:
    market_id: str
    outcome_id: str
    size: float
    average_price: float
    realized_pnl: float = 0.0
