from __future__ import annotations

from datetime import UTC, datetime

from signals.types import Signal


class OrderbookImbalanceStrategy:
    name = "orderbook_imbalance"

    def generate(self) -> list[Signal]:
        return [
            Signal(
                strategy=self.name,
                market_id="demo-market",
                outcome_id="no",
                action="sell",
                confidence=0.55,
                explanation={"bid_ask_ratio": 1.4, "note": "liquidity_shock"},
                created_at=datetime.now(UTC),
            )
        ]
