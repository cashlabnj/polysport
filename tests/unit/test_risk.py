from datetime import datetime

from risk.engine import RiskEngine
from signals.types import Signal


def test_set_limit_rejects_negative() -> None:
    engine = RiskEngine()
    assert engine.set_limit("max_order_size", -1.0) is False


def test_set_limit_casts_int() -> None:
    engine = RiskEngine()
    assert engine.set_limit("max_open_positions", 7.8) is True
    assert engine.limits.max_open_positions == 7


def test_set_limit_strategy_cap() -> None:
    engine = RiskEngine()
    assert engine.set_limit("strategy.vegas_value", 12.5) is True
    assert engine.limits.strategy_caps == {"vegas_value": 12.5}


def test_rejects_order_above_cap() -> None:
    engine = RiskEngine()
    engine.set_limit("max_order_size", 5.0)
    signal = Signal(
        strategy="vegas_value",
        market_id="demo-market",
        outcome_id="yes",
        action="buy",
        size=10.0,
        confidence=0.8,
        explanation={"edge": 0.2},
        created_at=datetime.utcnow(),
    )
    decision = engine.evaluate(signal, current_positions=0)
    assert decision.approved is False
    assert decision.reason == "order_size_above_cap"
