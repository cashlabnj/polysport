from __future__ import annotations

import statistics
from datetime import UTC, datetime

from signals.types import MarketSnapshot, OutcomeSnapshot, Signal


class MeanReversionStrategy:
    """
    Mean Reversion Strategy.

    Identifies markets where prices have deviated significantly from their
    recent average, suggesting a potential reversion to the mean.

    Logic:
    - Calculate rolling mean and std deviation of prices
    - Compute z-score (how many stds from mean)
    - If z-score < -1.5: price is oversold, signal BUY
    - If z-score > 1.5: price is overbought, signal SELL
    """

    name = "mean_reversion"
    MIN_HISTORY = 5  # Minimum price points needed
    Z_THRESHOLD = 1.5  # Standard deviations from mean
    MIN_CONFIDENCE = 0.6

    def generate(self, markets: list[MarketSnapshot] | None = None) -> list[Signal]:
        """Generate signals based on mean reversion analysis."""
        if not markets:
            return []

        signals = []
        for market in markets:
            for outcome in market.outcomes:
                signal = self._analyze_outcome(market, outcome)
                if signal:
                    signals.append(signal)

        return signals

    def _analyze_outcome(
        self, market: MarketSnapshot, outcome: OutcomeSnapshot
    ) -> Signal | None:
        """Analyze a single outcome for mean reversion opportunity."""
        if not isinstance(outcome, OutcomeSnapshot):
            return None

        # Need sufficient price history
        prices = outcome.price_history
        if len(prices) < self.MIN_HISTORY:
            return None

        # Calculate statistics
        mean_price = statistics.mean(prices)
        std_dev = statistics.stdev(prices)
        if std_dev < 0.01:  # Not enough variance
            return None

        current_price = outcome.current_price
        z_score = (current_price - mean_price) / std_dev

        # Check for significant deviation
        if abs(z_score) < self.Z_THRESHOLD:
            return None

        # Determine action: buy if oversold (negative z), sell if overbought (positive z)
        action = "buy" if z_score < -self.Z_THRESHOLD else "sell"
        confidence = min(0.8, self.MIN_CONFIDENCE + abs(z_score) * 0.05)

        return Signal(
            strategy=self.name,
            market_id=market.market_id,
            outcome_id=outcome.outcome_id,
            action=action,
            confidence=round(confidence, 2),
            explanation={
                "z_score": round(z_score, 2),
                "mean_price": round(mean_price, 3),
                "current_price": round(current_price, 3),
                "std_dev": round(std_dev, 3),
                "data_points": len(prices),
            },
            created_at=datetime.now(UTC),
        )
