from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, List, Optional

from polymarket.models import Fill, Market, Order, Outcome, Position


@dataclass
class ClientConfig:
    api_base: str
    api_key: Optional[str]
    wallet_address: Optional[str]
    paper: bool = True


class PolymarketClient:
    def __init__(self, config: ClientConfig) -> None:
        self.config = config

    @classmethod
    def from_env(cls) -> "PolymarketClient":
        return cls(
            ClientConfig(
                api_base="https://example.polymarket.com",
                api_key=None,
                wallet_address=None,
                paper=True,
            )
        )

    def get_markets(self) -> List[Market]:
        return [
            Market(
                id="demo-market",
                question="Will Team A win?",
                outcomes=[Outcome(id="yes", name="Yes", price=0.52), Outcome(id="no", name="No", price=0.48)],
                active=True,
            )
        ]

    def get_market(self, market_id: str) -> Market:
        markets = {market.id: market for market in self.get_markets()}
        return markets[market_id]

    def place_order(self, order: Order) -> Order:
        return Order(
            id=order.id,
            market_id=order.market_id,
            outcome_id=order.outcome_id,
            side=order.side,
            price=order.price,
            size=order.size,
            status="accepted" if self.config.paper else "submitted",
            created_at=order.created_at,
        )

    def get_fills(self, order_id: Optional[str] = None) -> List[Fill]:
        fills = [
            Fill(
                id="fill-1",
                order_id="order-1",
                market_id="demo-market",
                outcome_id="yes",
                price=0.52,
                size=5.0,
                timestamp=datetime.now(timezone.utc),
            )
        ]
        if order_id:
            return [fill for fill in fills if fill.order_id == order_id]
        return fills

    def get_positions(self) -> List[Position]:
        return [
            Position(
                market_id="demo-market",
                outcome_id="yes",
                size=5.0,
                average_price=0.52,
            )
        ]

    def health(self) -> Dict[str, str]:
        return {"status": "ok", "mode": "paper" if self.config.paper else "live"}
