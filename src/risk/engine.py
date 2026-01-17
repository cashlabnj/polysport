from __future__ import annotations

from dataclasses import dataclass
from typing import List

from risk.limits import RiskLimits
from signals.types import Signal


@dataclass
class RiskDecision:
    approved: bool
    reason: str


class RiskEngine:
    def __init__(self, limits: RiskLimits | None = None) -> None:
        self.limits = limits or RiskLimits()
        self.trading_enabled = True

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

    def evaluate(self, signal: Signal, current_positions: int, current_position_size: float = 0.0) -> RiskDecision:
        if not self.trading_enabled:
            return RiskDecision(False, "global_kill_switch")
        if current_positions >= self.limits.max_open_positions:
            return RiskDecision(False, "max_open_positions")
        cap = min(self.limits.max_order_size, self.limits.cap_for_strategy(signal.strategy))
        if signal.size > cap:
            return RiskDecision(False, "order_size_above_cap")
        if current_position_size + signal.size > self.limits.max_position_size:
            return RiskDecision(False, "max_position_size")
        if signal.confidence < 0.4:
            return RiskDecision(False, "confidence_below_threshold")
        return RiskDecision(True, "approved")

    def batch_evaluate(
        self,
        signals: List[Signal],
        current_positions: int,
        current_position_size: float = 0.0,
    ) -> List[RiskDecision]:
        return [self.evaluate(signal, current_positions, current_position_size) for signal in signals]
