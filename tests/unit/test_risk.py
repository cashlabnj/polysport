from risk.engine import RiskEngine


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
