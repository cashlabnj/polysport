from __future__ import annotations

from datetime import UTC, datetime

from signals.types import Signal


class HedgedPortfolioStrategy:
    name = "hedged_portfolio"

    def generate(self) -> list[Signal]:
        return [
            Signal(
                strategy=self.name,
                market_id="demo-market",
                outcome_id="yes",
                action="buy",
                confidence=0.45,
                explanation={"hedge_ratio": 0.6, "note": "correlated_outcomes"},
                created_at=datetime.now(UTC),
            )
        ]
