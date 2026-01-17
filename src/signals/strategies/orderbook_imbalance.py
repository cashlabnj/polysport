from __future__ import annotations

from typing import TYPE_CHECKING

from signals.types import Signal

if TYPE_CHECKING:
    from signals.types import MarketSnapshot


class OrderbookImbalanceStrategy:
    """
    Orderbook Imbalance Strategy.

    Analyzes order book depth to detect buy/sell pressure imbalances.
    Requires real-time CLOB (Central Limit Order Book) data.

    Currently returns empty signals until orderbook data is integrated.
    """

    name = "orderbook_imbalance"

    def generate(self, markets: list[MarketSnapshot] | None = None) -> list[Signal]:
        """Generate signals based on orderbook analysis.

        Note: This strategy requires real-time orderbook data.
        Returns empty list until that integration is complete.
        """
        # TODO: Integrate with Polymarket CLOB WebSocket
        # to analyze bid/ask depth and order flow
        return []
