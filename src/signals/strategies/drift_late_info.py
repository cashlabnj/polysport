from __future__ import annotations

from datetime import UTC, datetime

from signals.types import MarketSnapshot, OutcomeSnapshot, Signal


class LateInfoDriftStrategy:
    """
    Late Information Drift Strategy.

    Identifies markets where prices are drifting in a direction as the
    event approaches, suggesting informed trading or late-breaking information.

    Logic:
    - Only consider markets closing within 24 hours
    - Calculate price drift (change from recent history)
    - If significant drift detected near event, follow the momentum
    - Higher confidence for larger drifts closer to event
    """

    name = "late_information_drift"
    MAX_HOURS_TO_EVENT = 24  # Only analyze markets closing within this window
    MIN_HOURS_TO_EVENT = 1  # Avoid markets about to close (too risky)
    MIN_DRIFT = 0.03  # Minimum 3% price movement to consider
    MIN_CONFIDENCE = 0.6

    def generate(self, markets: list[MarketSnapshot] | None = None) -> list[Signal]:
        """Generate signals based on late information drift analysis."""
        if not markets:
            return []

        signals = []
        now = datetime.now(UTC)

        for market in markets:
            # Skip markets without close time
            if not market.close_time:
                continue

            # Calculate time to event
            time_to_event = market.close_time - now
            hours_to_event = time_to_event.total_seconds() / 3600

            # Only analyze markets in the right time window
            if hours_to_event < self.MIN_HOURS_TO_EVENT:
                continue
            if hours_to_event > self.MAX_HOURS_TO_EVENT:
                continue

            for outcome in market.outcomes:
                signal = self._analyze_drift(market, outcome, hours_to_event)
                if signal:
                    signals.append(signal)

        return signals

    def _analyze_drift(
        self,
        market: MarketSnapshot,
        outcome: OutcomeSnapshot,
        hours_to_event: float,
    ) -> Signal | None:
        """Analyze price drift for a single outcome."""
        if not isinstance(outcome, OutcomeSnapshot):
            return None

        prices = outcome.price_history
        if len(prices) < 2:
            return None

        # Calculate drift: difference between current and oldest price
        oldest_price = prices[0]
        current_price = outcome.current_price

        if oldest_price == 0:
            return None

        drift = current_price - oldest_price
        drift_pct = abs(drift) / oldest_price

        # Check if drift is significant
        if drift_pct < self.MIN_DRIFT:
            return None

        # Determine action: follow the drift direction
        action = "buy" if drift > 0 else "sell"

        # Calculate confidence based on drift magnitude and time proximity
        # Higher drift = higher confidence
        # Closer to event = higher confidence
        time_factor = 1 - (hours_to_event / self.MAX_HOURS_TO_EVENT)  # 0-1
        drift_factor = min(drift_pct / 0.10, 1.0)  # Cap at 10% drift

        confidence = self.MIN_CONFIDENCE + (time_factor * 0.1) + (drift_factor * 0.1)
        confidence = min(0.8, confidence)

        return Signal(
            strategy=self.name,
            market_id=market.market_id,
            outcome_id=outcome.outcome_id,
            action=action,
            confidence=round(confidence, 2),
            explanation={
                "drift": round(drift, 3),
                "drift_pct": round(drift_pct * 100, 1),
                "hours_to_event": round(hours_to_event, 1),
                "current_price": round(current_price, 3),
                "oldest_price": round(oldest_price, 3),
            },
            created_at=datetime.now(UTC),
        )
