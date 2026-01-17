from __future__ import annotations

from dataclasses import dataclass

from polymarket.client import PolymarketClient


@dataclass(frozen=True)
class HealthStatus:
    status: str
    mode: str


def check_health(client: PolymarketClient) -> HealthStatus:
    data = client.health()
    return HealthStatus(status=data["status"], mode=data["mode"])
