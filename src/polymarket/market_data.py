from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from polymarket.client import PolymarketClient
from polymarket.models import Market


@dataclass
class MarketSnapshot:
    market: Market
    captured_at: datetime


class MarketDataService:
    def __init__(self, client: PolymarketClient) -> None:
        self.client = client

    def snapshot(self) -> list[MarketSnapshot]:
        now = datetime.now(UTC)
        return [MarketSnapshot(market=market, captured_at=now) for market in self.client.get_markets()]
