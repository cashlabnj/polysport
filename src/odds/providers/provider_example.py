from __future__ import annotations

from datetime import datetime

from odds.providers.provider_base import OddsProvider, OddsSnapshot


class ExampleOddsProvider(OddsProvider):
    def fetch(self) -> list[OddsSnapshot]:
        return [
            OddsSnapshot(
                market_id="demo-market",
                outcomes={"yes": 0.51, "no": 0.49},
                captured_at=datetime.utcnow(),
            )
        ]
