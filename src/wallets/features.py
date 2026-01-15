from __future__ import annotations

from dataclasses import dataclass
from typing import Dict


@dataclass(frozen=True)
class WalletFeatures:
    roi: float
    win_rate: float
    drawdown_proxy: float
    timing_edge: float
    market_selectivity: float

    def as_dict(self) -> Dict[str, float]:
        return {
            "roi": self.roi,
            "win_rate": self.win_rate,
            "drawdown_proxy": self.drawdown_proxy,
            "timing_edge": self.timing_edge,
            "market_selectivity": self.market_selectivity,
        }
