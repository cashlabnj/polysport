from datetime import datetime, timezone

import pytest

from execution.engine import ExecutionEngine, ExecutionResult, OrderSizing
from risk.engine import RiskDecision
from signals.types import Signal


def _make_signal(
    confidence: float = 0.7,
    strategy: str = "test_strategy",
    market_id: str = "test-market",
    action: str = "buy",
    edge: float = 0.03,
) -> Signal:
    return Signal(
        strategy=strategy,
        market_id=market_id,
        outcome_id="yes",
        action=action,
        confidence=confidence,
        explanation={"edge": edge},
        created_at=datetime.now(timezone.utc),
    )


class TestExecutionEngineSubmit:
    def test_rejects_unapproved_decision(self) -> None:
        engine = ExecutionEngine()
        signal = _make_signal()
        decision = RiskDecision(approved=False, reason="test_rejection")
        result = engine.submit(signal, decision)
        assert result.status == "rejected"
        assert result.reason == "test_rejection"
        assert result.order is None

    def test_approves_and_creates_order(self) -> None:
        engine = ExecutionEngine()
        signal = _make_signal()
        decision = RiskDecision(approved=True, reason="approved")
        result = engine.submit(signal, decision)
        assert result.status == "submitted"
        assert result.reason == "ok"
        assert result.order is not None
        assert result.order.market_id == "test-market"
        assert result.order.status == "paper"  # Default is paper mode

    def test_prevents_duplicate_orders(self) -> None:
        engine = ExecutionEngine()
        signal = _make_signal()
        decision = RiskDecision(approved=True, reason="approved")

        result1 = engine.submit(signal, decision)
        assert result1.status == "submitted"

        result2 = engine.submit(signal, decision)
        assert result2.status == "duplicate"
        assert result2.reason == "idempotent_key"

    def test_calculates_price_from_edge(self) -> None:
        engine = ExecutionEngine()
        signal = _make_signal(action="buy", edge=0.05)
        decision = RiskDecision(approved=True, reason="approved")
        result = engine.submit(signal, decision)
        assert result.order is not None
        assert result.order.price == 0.55  # 0.5 + 0.05 edge

    def test_calculates_size_from_confidence(self) -> None:
        engine = ExecutionEngine(sizing=OrderSizing(base_size=10.0))
        signal = _make_signal(confidence=0.8)  # Higher confidence = larger size
        decision = RiskDecision(approved=True, reason="approved")
        result = engine.submit(signal, decision)
        assert result.order is not None
        # Size should be scaled based on confidence
        assert result.order.size > 0

    def test_rejects_slippage_exceeded(self) -> None:
        engine = ExecutionEngine()
        signal = _make_signal(edge=0.03)  # Target price = 0.53
        decision = RiskDecision(approved=True, reason="approved")
        # Current price is very different from target
        result = engine.submit(signal, decision, current_price=0.60)
        assert result.status == "rejected"
        assert "slippage_exceeded" in result.reason

    def test_live_mode_status(self) -> None:
        engine = ExecutionEngine()
        engine.set_paper(False)
        signal = _make_signal()
        decision = RiskDecision(approved=True, reason="approved")
        result = engine.submit(signal, decision)
        assert result.order is not None
        assert result.order.status == "submitted"  # Not "paper"


class TestExecutionEngineOrders:
    def test_get_open_orders_empty(self) -> None:
        engine = ExecutionEngine()
        orders = engine.get_open_orders()
        assert orders == []

    def test_get_open_orders_returns_orders(self) -> None:
        engine = ExecutionEngine()
        signal = _make_signal()
        decision = RiskDecision(approved=True, reason="approved")
        engine.submit(signal, decision)
        orders = engine.get_open_orders()
        assert len(orders) == 1

    def test_cancel_order(self) -> None:
        engine = ExecutionEngine()
        signal = _make_signal()
        decision = RiskDecision(approved=True, reason="approved")
        result = engine.submit(signal, decision)
        assert result.order is not None

        cancelled = engine.cancel_order(result.order.order_id)
        assert cancelled is True

    def test_cancel_nonexistent_order(self) -> None:
        engine = ExecutionEngine()
        cancelled = engine.cancel_order("nonexistent-order")
        assert cancelled is False


class TestOrderSizing:
    def test_default_values(self) -> None:
        sizing = OrderSizing()
        assert sizing.base_size == 10.0
        assert sizing.confidence_scaling is True
        assert sizing.min_size == 1.0
        assert sizing.max_size == 100.0
