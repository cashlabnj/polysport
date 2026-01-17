from __future__ import annotations

from datetime import datetime

from signals.types import Signal


class VegasValueStrategy:
    name = "vegas_value"

    def generate(self) -> list[Signal]:
        return [
            Signal(
                strategy=self.name,
                market_id="demo-market",
                outcome_id="yes",
                action="buy",
                size=10.0,
                confidence=0.62,
                explanation={"edge": 0.03, "source": "vegas_vs_poly"},
                created_at=datetime.utcnow(),
            )
        ]
