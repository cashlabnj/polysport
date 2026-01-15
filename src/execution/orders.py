from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class ExecutionOrder:
    order_id: str
    market_id: str
    outcome_id: str
    side: str
    price: float
    size: float
    status: str
    created_at: datetime
