from __future__ import annotations

import contextlib
import logging
from dataclasses import dataclass
from datetime import UTC, datetime

import httpx

from polymarket.models import Fill, Market, Order, Outcome, Position

logger = logging.getLogger(__name__)


def _parse_iso_datetime(iso_str: str | None) -> datetime | None:
    """Parse ISO datetime string, returning None on failure."""
    if not iso_str:
        return None
    with contextlib.suppress(ValueError):
        return datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
    return None

GAMMA_API_BASE = "https://gamma-api.polymarket.com"


@dataclass
class ClientConfig:
    api_base: str
    api_key: str | None
    wallet_address: str | None
    paper: bool = True


class PolymarketClient:
    def __init__(self, config: ClientConfig) -> None:
        self.config = config
        self._http = httpx.Client(timeout=10.0)

    @classmethod
    def from_env(cls) -> PolymarketClient:
        return cls(
            ClientConfig(
                api_base=GAMMA_API_BASE,
                api_key=None,
                wallet_address=None,
                paper=True,
            )
        )

    def get_markets(self, limit: int = 10, active: bool = True) -> list[Market]:
        """Fetch real markets from Polymarket Gamma API."""
        try:
            params = {
                "limit": limit,
                "active": str(active).lower(),
                "closed": "false",
            }
            response = self._http.get(f"{GAMMA_API_BASE}/markets", params=params)
            response.raise_for_status()
            data = response.json()

            markets = []
            for item in data:
                outcomes = []
                tokens = item.get("tokens", [])
                for token in tokens:
                    outcomes.append(
                        Outcome(
                            id=token.get("token_id", ""),
                            name=token.get("outcome", "Unknown"),
                            price=float(token.get("price", 0.5)),
                        )
                    )

                close_time = _parse_iso_datetime(item.get("end_date_iso"))

                markets.append(
                    Market(
                        id=item.get("condition_id", item.get("id", "")),
                        question=item.get("question", "Unknown"),
                        outcomes=outcomes,
                        active=item.get("active", False),
                        close_time=close_time,
                    )
                )
            return markets

        except httpx.HTTPError as e:
            logger.error(f"Failed to fetch markets: {e}")
            return self._get_demo_markets()

    def get_sports_markets(self, limit: int = 10) -> list[Market]:
        """Fetch sports-related markets from Polymarket."""
        try:
            params = {
                "limit": 100,
                "active": "true",
                "closed": "false",
            }
            response = self._http.get(f"{GAMMA_API_BASE}/markets", params=params)
            response.raise_for_status()
            data = response.json()

            sports_keywords = [
                "nfl", "nba", "mlb", "nhl", "soccer", "football", "basketball",
                "baseball", "hockey", "super bowl", "world series", "championship",
                "playoffs", "finals", "win", "game", "match", "team", "player",
                "sports", "ufc", "boxing", "tennis", "golf", "olympics"
            ]

            markets = []
            for item in data:
                question = item.get("question", "").lower()
                if any(kw in question for kw in sports_keywords):
                    outcomes = []
                    tokens = item.get("tokens", [])
                    for token in tokens:
                        outcomes.append(
                            Outcome(
                                id=token.get("token_id", ""),
                                name=token.get("outcome", "Unknown"),
                                price=float(token.get("price", 0.5)),
                            )
                        )

                    close_time = _parse_iso_datetime(item.get("end_date_iso"))

                    markets.append(
                        Market(
                            id=item.get("condition_id", item.get("id", "")),
                            question=item.get("question", "Unknown"),
                            outcomes=outcomes,
                            active=item.get("active", False),
                            close_time=close_time,
                        )
                    )

                    if len(markets) >= limit:
                        break

            return markets if markets else self._get_demo_markets()

        except httpx.HTTPError as e:
            logger.error(f"Failed to fetch sports markets: {e}")
            return self._get_demo_markets()

    def _get_demo_markets(self) -> list[Market]:
        """Fallback demo markets when API is unavailable."""
        return [
            Market(
                id="demo-market",
                question="Will Team A win? (Demo)",
                outcomes=[
                    Outcome(id="yes", name="Yes", price=0.52),
                    Outcome(id="no", name="No", price=0.48),
                ],
                active=True,
            )
        ]

    def get_market(self, market_id: str) -> Market | None:
        """Fetch a specific market by ID."""
        try:
            response = self._http.get(f"{GAMMA_API_BASE}/markets/{market_id}")
            response.raise_for_status()
            item = response.json()

            outcomes = []
            tokens = item.get("tokens", [])
            for token in tokens:
                outcomes.append(
                    Outcome(
                        id=token.get("token_id", ""),
                        name=token.get("outcome", "Unknown"),
                        price=float(token.get("price", 0.5)),
                    )
                )

            close_time = _parse_iso_datetime(item.get("end_date_iso"))

            return Market(
                id=item.get("condition_id", item.get("id", "")),
                question=item.get("question", "Unknown"),
                outcomes=outcomes,
                active=item.get("active", False),
                close_time=close_time,
            )

        except httpx.HTTPError as e:
            logger.error(f"Failed to fetch market {market_id}: {e}")
            return None

    def place_order(self, order: Order) -> Order:
        """Place an order (paper mode only for now)."""
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

    def get_fills(self, order_id: str | None = None) -> list[Fill]:
        """Get fills (paper mode returns demo data)."""
        fills = [
            Fill(
                id="fill-1",
                order_id="order-1",
                market_id="demo-market",
                outcome_id="yes",
                price=0.52,
                size=5.0,
                timestamp=datetime.now(UTC),
            )
        ]
        if order_id:
            return [fill for fill in fills if fill.order_id == order_id]
        return fills

    def get_positions(self) -> list[Position]:
        """Get positions (paper mode returns demo data)."""
        return [
            Position(
                market_id="demo-market",
                outcome_id="yes",
                size=5.0,
                average_price=0.52,
            )
        ]

    def health(self) -> dict[str, str]:
        """Check API health."""
        try:
            response = self._http.get(f"{GAMMA_API_BASE}/markets", params={"limit": 1})
            response.raise_for_status()
            return {"status": "ok", "mode": "paper" if self.config.paper else "live"}
        except httpx.HTTPError:
            return {"status": "degraded", "mode": "paper" if self.config.paper else "live"}
