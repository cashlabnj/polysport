from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from execution.orders import ExecutionOrder
from execution.slippage import within_slippage
from risk.engine import RiskDecision
from risk.limits import RiskLimits
from signals.types import Signal

if TYPE_CHECKING:
    from storage.db import Database


# Default sizing parameters
DEFAULT_ORDER_SIZE = 10.0
DEFAULT_MAX_SLIPPAGE = 0.02  # 2%


@dataclass
class ExecutionResult:
    order: ExecutionOrder | None
    status: str
    reason: str


@dataclass
class OrderSizing:
    """Parameters for order sizing calculation."""
    base_size: float = DEFAULT_ORDER_SIZE
    confidence_scaling: bool = True
    min_size: float = 1.0
    max_size: float = 100.0


class ExecutionEngine:
    def __init__(
        self,
        db: "Database | None" = None,
        limits: RiskLimits | None = None,
        sizing: OrderSizing | None = None,
    ) -> None:
        self.db = db
        self.limits = limits or RiskLimits()
        self.sizing = sizing or OrderSizing()
        self.paper = True
        # In-memory fallback for idempotency (use DB when available)
        self._idempotency_keys: set[str] = set()
        self._open_orders: dict[str, ExecutionOrder] = {}

    def set_paper(self, paper: bool) -> None:
        self.paper = paper
        if self.db:
            self.db.set_paper_mode(paper)

    def _generate_order_id(self) -> str:
        """Generate unique order ID."""
        return f"order-{uuid.uuid4().hex[:12]}"

    def _calculate_order_size(self, signal: Signal) -> float:
        """Calculate order size based on signal and sizing rules."""
        size = self.sizing.base_size

        # Scale by confidence if enabled
        if self.sizing.confidence_scaling:
            # Higher confidence = larger position
            # Scale from 0.5x at 0.6 confidence to 2x at 1.0 confidence
            confidence_factor = 0.5 + (signal.confidence - 0.6) * (1.5 / 0.4)
            confidence_factor = max(0.5, min(2.0, confidence_factor))
            size *= confidence_factor

        # Apply strategy cap if defined
        strategy_cap = self.limits.cap_for_strategy(signal.strategy)
        size = min(size, strategy_cap)

        # Apply absolute limits
        size = max(self.sizing.min_size, min(self.sizing.max_size, size))

        return round(size, 2)

    def _get_target_price(self, signal: Signal) -> float:
        """Get target price from signal explanation or use default."""
        explanation = signal.explanation
        if "target_price" in explanation:
            return float(explanation["target_price"])
        if "edge" in explanation:
            # Estimate price based on edge (simplified)
            edge = float(explanation["edge"])
            if signal.action == "buy":
                return 0.5 + edge  # Buy at fair value + edge
            return 0.5 - edge  # Sell at fair value - edge
        return 0.5  # Default price

    def _check_idempotency(self, key: str) -> bool:
        """Check if idempotency key exists."""
        if self.db:
            return self.db.check_idempotency_key(key)
        return key in self._idempotency_keys

    def _save_idempotency(self, key: str) -> None:
        """Save idempotency key."""
        if self.db:
            self.db.add_idempotency_key(key)
        else:
            self._idempotency_keys.add(key)

    def submit(
        self,
        signal: Signal,
        decision: RiskDecision,
        current_price: float | None = None,
    ) -> ExecutionResult:
        """Submit an order for execution.

        Args:
            signal: The trading signal
            decision: Risk decision (must be approved)
            current_price: Current market price for slippage check
        """
        if not decision.approved:
            return ExecutionResult(order=None, status="rejected", reason=decision.reason)

        # Generate idempotency key
        key = f"{signal.strategy}:{signal.market_id}:{signal.outcome_id}:{signal.action}"
        if self._check_idempotency(key):
            return ExecutionResult(order=None, status="duplicate", reason="idempotent_key")

        # Calculate order parameters
        target_price = self._get_target_price(signal)
        order_size = self._calculate_order_size(signal)

        # Check slippage if current price is provided
        if current_price is not None:
            if not within_slippage(target_price, current_price, DEFAULT_MAX_SLIPPAGE):
                return ExecutionResult(
                    order=None,
                    status="rejected",
                    reason=f"slippage_exceeded: target={target_price:.3f}, current={current_price:.3f}",
                )

        # Save idempotency key BEFORE creating order (prevents duplicates on failure)
        self._save_idempotency(key)

        # Create order
        order = ExecutionOrder(
            order_id=self._generate_order_id(),
            market_id=signal.market_id,
            outcome_id=signal.outcome_id,
            side=signal.action,
            price=target_price,
            size=order_size,
            status="paper" if self.paper else "submitted",
            created_at=datetime.now(timezone.utc),
        )

        # Persist order
        if self.db:
            self.db.save_order(
                order_id=order.order_id,
                market_id=order.market_id,
                outcome_id=order.outcome_id,
                side=order.side,
                price=order.price,
                size=order.size,
                status=order.status,
                strategy=signal.strategy,
            )
        else:
            self._open_orders[order.order_id] = order

        return ExecutionResult(order=order, status="submitted", reason="ok")

    def cancel_order(self, order_id: str) -> bool:
        """Cancel an open order."""
        if self.db:
            self.db.update_order_status(order_id, "cancelled")
            return True
        if order_id in self._open_orders:
            del self._open_orders[order_id]
            return True
        return False

    def get_open_orders(self) -> list[ExecutionOrder]:
        """Get all open orders."""
        if self.db:
            order_dicts = self.db.get_open_orders()
            return [
                ExecutionOrder(
                    order_id=o["order_id"],
                    market_id=o["market_id"],
                    outcome_id=o["outcome_id"],
                    side=o["side"],
                    price=o["price"],
                    size=o["size"],
                    status=o["status"],
                    created_at=datetime.fromisoformat(o["created_at"]),
                )
                for o in order_dicts
            ]
        return list(self._open_orders.values())
