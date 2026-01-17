from __future__ import annotations

from datetime import UTC, datetime

from signals.types import Signal


class LateInfoDriftStrategy:
    name = "late_information_drift"

    def generate(self) -> list[Signal]:
        return [
            Signal(
                strategy=self.name,
                market_id="demo-market",
                outcome_id="yes",
                action="buy",
                confidence=0.57,
                explanation={"drift": 0.02, "time_to_event_hours": 6},
                created_at=datetime.now(UTC),
            )
        ]
