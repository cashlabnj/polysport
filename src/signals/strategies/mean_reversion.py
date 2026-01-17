from __future__ import annotations

from datetime import datetime, timezone

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
                confidence=0.5,
                explanation={"z_score": -1.5, "note": "overreaction"},
                created_at=datetime.now(timezone.utc),
            )
        ]
