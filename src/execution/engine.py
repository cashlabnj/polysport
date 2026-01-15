from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Set

from execution.orders import ExecutionOrder
from risk.engine import RiskDecision
from signals.types import Signal


@dataclass
class ExecutionResult:
    order: ExecutionOrder | None
    status: str
    reason: str


class ExecutionEngine:
    def __init__(self) -> None:
        self.paper = True
        self.idempotency_keys: Set[str] = set()
        self.open_orders: Dict[str, ExecutionOrder] = {}

    def set_paper(self, paper: bool) -> None:
        self.paper = paper

    def submit(self, signal: Signal, decision: RiskDecision) -> ExecutionResult:
        if not decision.approved:
            return ExecutionResult(order=None, status="rejected", reason=decision.reason)
        key = f"{signal.strategy}:{signal.market_id}:{signal.outcome_id}:{signal.action}"
        if key in self.idempotency_keys:
            return ExecutionResult(order=None, status="duplicate", reason="idempotent_key")
        self.idempotency_keys.add(key)
        order = ExecutionOrder(
            order_id=f"order-{len(self.idempotency_keys)}",
            market_id=signal.market_id,
            outcome_id=signal.outcome_id,
            side=signal.action,
            price=0.5,
            size=10.0,
            status="paper" if self.paper else "submitted",
            created_at=datetime.utcnow(),
        )
        self.open_orders[order.order_id] = order
        return ExecutionResult(order=order, status="submitted", reason="ok")
