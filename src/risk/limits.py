from __future__ import annotations

from dataclasses import dataclass


@dataclass
class RiskLimits:
    max_position_size: float = 100.0
    max_order_size: float = 50.0
    max_open_positions: int = 10
    max_daily_loss: float = 100.0
    strategy_caps: dict[str, float] | None = None

    def cap_for_strategy(self, strategy: str) -> float:
        if self.strategy_caps and strategy in self.strategy_caps:
            return self.strategy_caps[strategy]
        return self.max_order_size
