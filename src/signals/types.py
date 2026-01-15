from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List


@dataclass(frozen=True)
class Signal:
    strategy: str
    market_id: str
    outcome_id: str
    action: str
    confidence: float
    explanation: Dict[str, float | str]
    created_at: datetime


@dataclass(frozen=True)
class SignalBatch:
    signals: List[Signal]
    created_at: datetime
