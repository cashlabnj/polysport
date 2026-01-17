from __future__ import annotations

from typing import TYPE_CHECKING

from signals.types import Signal

if TYPE_CHECKING:
    from signals.types import MarketSnapshot


class VegasValueStrategy:
    """
    Vegas Value Strategy.

    Compares Polymarket prices to sportsbook odds to find value.
    Requires external sportsbook API (The Odds API, etc.) to function.

    Currently returns empty signals until sportsbook data is integrated.
    """

    name = "vegas_value"

    def generate(self, markets: list[MarketSnapshot] | None = None) -> list[Signal]:
        """Generate signals based on Vegas odds comparison.

        Note: This strategy requires external sportsbook data.
        Returns empty list until that integration is complete.
        """
        # TODO: Integrate with The Odds API or similar service
        # to compare Polymarket prices with Vegas/sportsbook odds
        return []
