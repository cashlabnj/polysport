from __future__ import annotations

from typing import TYPE_CHECKING

from signals.types import Signal

if TYPE_CHECKING:
    from signals.types import MarketSnapshot


class SmartMoneyConfirmStrategy:
    """
    Smart Money Confirmation Strategy.

    Tracks high-performing wallets and follows their trades.
    Requires blockchain data (Etherscan API, TheGraph) to function.

    Currently returns empty signals until wallet tracking is integrated.
    """

    name = "smart_money_confirm"

    def generate(self, markets: list[MarketSnapshot] | None = None) -> list[Signal]:
        """Generate signals based on smart money wallet tracking.

        Note: This strategy requires blockchain wallet data.
        Returns empty list until that integration is complete.
        """
        # TODO: Integrate with Etherscan/TheGraph to track
        # high-performing wallet addresses and their trades
        return []
