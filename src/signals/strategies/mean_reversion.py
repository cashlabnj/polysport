from __future__ import annotations

from datetime import datetime

from signals.types import Signal


class MeanReversionStrategy:
    name = "mean_reversion"

    def generate(self) -> list[Signal]:
        return [
            Signal(
                strategy=self.name,
                market_id="demo-market",
                outcome_id="no",
                action="buy",
                size=6.0,
                confidence=0.5,
                explanation={"z_score": -1.5, "note": "overreaction"},
                created_at=datetime.utcnow(),
            )
        ]
