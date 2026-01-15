from __future__ import annotations

from dataclasses import dataclass

from wallets.features import WalletFeatures


@dataclass(frozen=True)
class WalletScore:
    wallet: str
    score: float
    features: WalletFeatures


class WalletScoringEngine:
    def __init__(self, weights: dict[str, float] | None = None) -> None:
        self.weights = weights or {
            "roi": 0.35,
            "win_rate": 0.2,
            "drawdown_proxy": 0.15,
            "timing_edge": 0.2,
            "market_selectivity": 0.1,
        }

    def score(self, wallet: str, features: WalletFeatures) -> WalletScore:
        total = sum(features.as_dict()[key] * weight for key, weight in self.weights.items())
        return WalletScore(wallet=wallet, score=total, features=features)
