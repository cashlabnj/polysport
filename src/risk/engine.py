from __future__ import annotations

from dataclasses import dataclass

from risk.limits import RiskLimits
from signals.types import Signal

# Minimum confidence threshold for trade approval
MIN_CONFIDENCE_THRESHOLD = 0.6


@dataclass
class RiskDecision:
    approved: bool
    reason: str


@dataclass
class RiskState:
    """Tracks current risk state for evaluation."""
    current_positions: int = 0
    daily_pnl: float = 0.0
    position_sizes: dict[str, float] | None = None

    def position_size(self, market_id: str) -> float:
        if self.position_sizes is None:
            return 0.0
        return self.position_sizes.get(market_id, 0.0)


class RiskEngine:
    def __init__(self, limits: RiskLimits | None = None) -> None:
        self.limits = limits or RiskLimits()
        # SAFE DEFAULT: Trading OFF until explicitly enabled
        self.trading_enabled = False

    def set_trading(self, enabled: bool) -> None:
        self.trading_enabled = enabled

    def set_limit(self, param: str, value: float) -> bool:
        if value < 0:
            return False
        if param.startswith("strategy."):
            strategy = param.split("strategy.", 1)[1]
            if not strategy:
                return False
            if self.limits.strategy_caps is None:
                self.limits.strategy_caps = {}
            self.limits.strategy_caps[strategy] = value
            return True
        if hasattr(self.limits, param):
            current = getattr(self.limits, param)
            if isinstance(current, int):
                setattr(self.limits, param, int(value))
            else:
                setattr(self.limits, param, value)
            return True
        return False

    def evaluate(
        self,
        signal: Signal,
        current_positions: int,
        daily_pnl: float = 0.0,
        order_size: float = 0.0,
        position_size: float = 0.0,
    ) -> RiskDecision:
        """Evaluate a signal against all risk limits.

        Args:
            signal: The trading signal to evaluate
            current_positions: Number of currently open positions
            daily_pnl: Current day's profit/loss (negative = loss)
            order_size: Size of the proposed order
            position_size: Current position size in this market
        """
        # Kill switch check
        if not self.trading_enabled:
            return RiskDecision(False, "global_kill_switch")

        # Daily loss limit check
        if daily_pnl <= -self.limits.max_daily_loss:
            return RiskDecision(False, "max_daily_loss_exceeded")

        # Order size check
        if order_size > 0 and order_size > self.limits.max_order_size:
            return RiskDecision(False, "order_size_exceeded")

        # Position size check (existing + new order)
        if position_size + order_size > self.limits.max_position_size:
            return RiskDecision(False, "max_position_size_exceeded")

        # Open positions limit check
        if current_positions >= self.limits.max_open_positions:
            return RiskDecision(False, "max_open_positions")

        # Strategy-specific cap check
        strategy_cap = self.limits.cap_for_strategy(signal.strategy)
        if order_size > 0 and order_size > strategy_cap:
            return RiskDecision(False, "strategy_cap_exceeded")

        # Confidence threshold check
        if signal.confidence < MIN_CONFIDENCE_THRESHOLD:
            return RiskDecision(False, "confidence_below_threshold")

        return RiskDecision(True, "approved")

    def evaluate_simple(self, signal: Signal, current_positions: int) -> RiskDecision:
        """Simplified evaluation for backward compatibility."""
        return self.evaluate(signal, current_positions)

    def batch_evaluate(
        self,
        signals: list[Signal],
        risk_state: RiskState | None = None,
    ) -> list[RiskDecision]:
        """Evaluate multiple signals against risk limits."""
        if risk_state is None:
            risk_state = RiskState()
        return [
            self.evaluate(
                signal,
                current_positions=risk_state.current_positions,
                daily_pnl=risk_state.daily_pnl,
            )
            for signal in signals
        ]
