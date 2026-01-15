from __future__ import annotations

from datetime import datetime
from typing import List

from signals.types import Signal, SignalBatch
from signals.strategies.vegas_value import VegasValueStrategy
from signals.strategies.smart_money_confirm import SmartMoneyConfirmStrategy
from signals.strategies.orderbook_imbalance import OrderbookImbalanceStrategy
from signals.strategies.drift_late_info import LateInfoDriftStrategy
from signals.strategies.mean_reversion import MeanReversionStrategy
from signals.strategies.hedged_portfolio import HedgedPortfolioStrategy


class SignalEngine:
    def __init__(self) -> None:
        self.strategies = [
            VegasValueStrategy(),
            SmartMoneyConfirmStrategy(),
            OrderbookImbalanceStrategy(),
            LateInfoDriftStrategy(),
            MeanReversionStrategy(),
            HedgedPortfolioStrategy(),
        ]

    def evaluate(self) -> SignalBatch:
        signals: List[Signal] = []
        for strategy in self.strategies:
            signals.extend(strategy.generate())
        return SignalBatch(signals=signals, created_at=datetime.utcnow())
