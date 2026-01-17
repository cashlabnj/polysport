from __future__ import annotations

from datetime import datetime

from signals.types import Signal


class SmartMoneyConfirmStrategy:
    name = "smart_money_confirm"

    def generate(self) -> list[Signal]:
        return [
            Signal(
                strategy=self.name,
                market_id="demo-market",
                outcome_id="yes",
                action="buy",
                size=10.0,
                confidence=0.58,
                explanation={"wallet_score": 0.8, "note": "top_wallets"},
                created_at=datetime.utcnow(),
            )
        ]
