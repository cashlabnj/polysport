from __future__ import annotations

from collections import defaultdict
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from signals.strategies.drift_late_info import LateInfoDriftStrategy
from signals.strategies.hedged_portfolio import HedgedPortfolioStrategy
from signals.strategies.mean_reversion import MeanReversionStrategy
from signals.strategies.orderbook_imbalance import OrderbookImbalanceStrategy
from signals.strategies.smart_money_confirm import SmartMoneyConfirmStrategy
from signals.strategies.vegas_value import VegasValueStrategy
from signals.types import MarketSnapshot, OutcomeSnapshot, Signal, SignalBatch

if TYPE_CHECKING:
    from polymarket.client import PolymarketClient


class SignalEngine:
    """Engine that evaluates all trading strategies against market data."""

    MAX_PRICE_HISTORY = 20  # Keep last 20 price points per outcome

    def __init__(self, polymarket: PolymarketClient | None = None) -> None:
        self.polymarket = polymarket
        self.strategies = [
            VegasValueStrategy(),
            SmartMoneyConfirmStrategy(),
            OrderbookImbalanceStrategy(),
            LateInfoDriftStrategy(),
            MeanReversionStrategy(),
            HedgedPortfolioStrategy(),
        ]
        # Store price history: {market_id: {outcome_id: [prices]}}
        self._price_history: dict[str, dict[str, list[float]]] = defaultdict(
            lambda: defaultdict(list)
        )

    def evaluate(self) -> SignalBatch:
        """Evaluate all strategies and return generated signals."""
        # Fetch current market data
        markets = self._fetch_market_snapshots()

        # Run all strategies
        signals: list[Signal] = []
        for strategy in self.strategies:
            try:
                strategy_signals = strategy.generate(markets)
                signals.extend(strategy_signals)
            except Exception:
                # Log error but continue with other strategies
                pass

        return SignalBatch(signals=signals, created_at=datetime.now(UTC))

    def _fetch_market_snapshots(self) -> list[MarketSnapshot]:
        """Fetch markets from Polymarket and convert to snapshots."""
        if not self.polymarket:
            return []

        try:
            # Fetch sports markets from Polymarket
            raw_markets = self.polymarket.get_sports_markets(limit=20)
        except Exception:
            return []

        snapshots = []
        now = datetime.now(UTC)

        for market in raw_markets:
            outcome_snapshots = []

            for outcome in market.outcomes:
                # Update price history
                market_history = self._price_history[market.id]
                outcome_history = market_history[outcome.id]

                # Add current price to history
                outcome_history.append(outcome.price)

                # Keep only last N prices
                if len(outcome_history) > self.MAX_PRICE_HISTORY:
                    outcome_history.pop(0)

                outcome_snapshots.append(
                    OutcomeSnapshot(
                        outcome_id=outcome.id,
                        name=outcome.name,
                        current_price=outcome.price,
                        price_history=list(outcome_history),
                    )
                )

            snapshots.append(
                MarketSnapshot(
                    market_id=market.id,
                    question=market.question,
                    outcomes=outcome_snapshots,
                    close_time=market.close_time,
                    last_updated=now,
                )
            )

        return snapshots

    def get_price_history_count(self) -> int:
        """Get total number of price points stored (for debugging)."""
        total = 0
        for market_data in self._price_history.values():
            for outcome_prices in market_data.values():
                total += len(outcome_prices)
        return total
