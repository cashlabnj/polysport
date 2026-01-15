from __future__ import annotations

from dataclasses import dataclass

from polymarket.client import PolymarketClient
from polymarket.models import Order


@dataclass
class PolymarketExecution:
    client: PolymarketClient

    def submit_order(self, order: Order) -> Order:
        return self.client.place_order(order)
