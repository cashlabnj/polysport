from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List

from wallets.features import WalletFeatures
from wallets.scoring import WalletScoringEngine, WalletScore


@dataclass
class WalletSnapshot:
    wallet: str
    features: WalletFeatures
    captured_at: datetime


@dataclass
class WalletWatchlist:
    wallets: Dict[str, WalletSnapshot] = field(default_factory=dict)

    def update(self, snapshot: WalletSnapshot) -> None:
        self.wallets[snapshot.wallet] = snapshot

    def top(self, scoring: WalletScoringEngine, limit: int = 10) -> List[WalletScore]:
        scores = [scoring.score(wallet, snapshot.features) for wallet, snapshot in self.wallets.items()]
        return sorted(scores, key=lambda item: item.score, reverse=True)[:limit]


class WalletTracker:
    def __init__(self, scoring: WalletScoringEngine | None = None) -> None:
        self.scoring = scoring or WalletScoringEngine()
        self.watchlist = WalletWatchlist()

    def ingest(self, wallet: str, features: WalletFeatures) -> WalletSnapshot:
        snapshot = WalletSnapshot(wallet=wallet, features=features, captured_at=datetime.now(timezone.utc))
        self.watchlist.update(snapshot)
        return snapshot

    def leaderboard(self, limit: int = 10) -> List[WalletScore]:
        return self.watchlist.top(self.scoring, limit=limit)
