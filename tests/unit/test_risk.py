from datetime import UTC, datetime

from risk.engine import MIN_CONFIDENCE_THRESHOLD, RiskDecision, RiskEngine, RiskState
from risk.limits import RiskLimits
from signals.types import Signal


def _make_signal(
    confidence: float = 0.7,
    strategy: str = "test_strategy",
    market_id: str = "test-market",
) -> Signal:
    return Signal(
        strategy=strategy,
        market_id=market_id,
        outcome_id="yes",
        action="buy",
        confidence=confidence,
        explanation={"test": "data"},
        created_at=datetime.now(UTC),
    )


class TestRiskEngineDefaults:
    def test_trading_disabled_by_default(self) -> None:
        engine = RiskEngine()
        assert engine.trading_enabled is False

    def test_confidence_threshold_is_0_6(self) -> None:
        assert MIN_CONFIDENCE_THRESHOLD == 0.6


class TestRiskEngineLimits:
    def test_set_limit_rejects_negative(self) -> None:
        engine = RiskEngine()
        assert engine.set_limit("max_order_size", -1.0) is False

    def test_set_limit_casts_int(self) -> None:
        engine = RiskEngine()
        assert engine.set_limit("max_open_positions", 7.8) is True
        assert engine.limits.max_open_positions == 7

    def test_set_limit_strategy_cap(self) -> None:
        engine = RiskEngine()
        assert engine.set_limit("strategy.vegas_value", 12.5) is True
        assert engine.limits.strategy_caps == {"vegas_value": 12.5}

    def test_set_limit_unknown_param(self) -> None:
        engine = RiskEngine()
        assert engine.set_limit("unknown_param", 10.0) is False


class TestRiskEngineEvaluate:
    def test_rejects_when_trading_disabled(self) -> None:
        engine = RiskEngine()
        signal = _make_signal()
        decision = engine.evaluate(signal, current_positions=0)
        assert decision.approved is False
        assert decision.reason == "global_kill_switch"

    def test_approves_when_trading_enabled(self) -> None:
        engine = RiskEngine()
        engine.set_trading(True)
        signal = _make_signal(confidence=0.7)
        decision = engine.evaluate(signal, current_positions=0)
        assert decision.approved is True
        assert decision.reason == "approved"

    def test_rejects_low_confidence(self) -> None:
        engine = RiskEngine()
        engine.set_trading(True)
        signal = _make_signal(confidence=0.5)  # Below 0.6 threshold
        decision = engine.evaluate(signal, current_positions=0)
        assert decision.approved is False
        assert decision.reason == "confidence_below_threshold"

    def test_rejects_max_positions_exceeded(self) -> None:
        engine = RiskEngine(limits=RiskLimits(max_open_positions=5))
        engine.set_trading(True)
        signal = _make_signal()
        decision = engine.evaluate(signal, current_positions=5)
        assert decision.approved is False
        assert decision.reason == "max_open_positions"

    def test_rejects_daily_loss_exceeded(self) -> None:
        engine = RiskEngine(limits=RiskLimits(max_daily_loss=100.0))
        engine.set_trading(True)
        signal = _make_signal()
        decision = engine.evaluate(signal, current_positions=0, daily_pnl=-100.0)
        assert decision.approved is False
        assert decision.reason == "max_daily_loss_exceeded"

    def test_rejects_order_size_exceeded(self) -> None:
        engine = RiskEngine(limits=RiskLimits(max_order_size=50.0))
        engine.set_trading(True)
        signal = _make_signal()
        decision = engine.evaluate(signal, current_positions=0, order_size=60.0)
        assert decision.approved is False
        assert decision.reason == "order_size_exceeded"

    def test_rejects_position_size_exceeded(self) -> None:
        engine = RiskEngine(limits=RiskLimits(max_position_size=100.0))
        engine.set_trading(True)
        signal = _make_signal()
        decision = engine.evaluate(
            signal, current_positions=0, position_size=80.0, order_size=30.0
        )
        assert decision.approved is False
        assert decision.reason == "max_position_size_exceeded"

    def test_rejects_strategy_cap_exceeded(self) -> None:
        limits = RiskLimits(strategy_caps={"test_strategy": 20.0})
        engine = RiskEngine(limits=limits)
        engine.set_trading(True)
        signal = _make_signal(strategy="test_strategy")
        decision = engine.evaluate(signal, current_positions=0, order_size=25.0)
        assert decision.approved is False
        assert decision.reason == "strategy_cap_exceeded"


class TestRiskEngineBatchEvaluate:
    def test_batch_evaluate_returns_list(self) -> None:
        engine = RiskEngine()
        engine.set_trading(True)
        signals = [_make_signal(confidence=0.7), _make_signal(confidence=0.8)]
        decisions = engine.batch_evaluate(signals)
        assert len(decisions) == 2
        assert all(isinstance(d, RiskDecision) for d in decisions)

    def test_batch_evaluate_with_risk_state(self) -> None:
        engine = RiskEngine()
        engine.set_trading(True)
        signals = [_make_signal(confidence=0.7)]
        risk_state = RiskState(current_positions=0, daily_pnl=0.0)
        decisions = engine.batch_evaluate(signals, risk_state)
        assert len(decisions) == 1
        assert decisions[0].approved is True


class TestRiskState:
    def test_default_values(self) -> None:
        state = RiskState()
        assert state.current_positions == 0
        assert state.daily_pnl == 0.0
        assert state.position_sizes is None

    def test_position_size_returns_zero_when_none(self) -> None:
        state = RiskState()
        assert state.position_size("any-market") == 0.0

    def test_position_size_returns_value(self) -> None:
        state = RiskState(position_sizes={"market-1": 50.0})
        assert state.position_size("market-1") == 50.0
        assert state.position_size("market-2") == 0.0
