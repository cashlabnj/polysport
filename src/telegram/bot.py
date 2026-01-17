from __future__ import annotations

from dataclasses import dataclass, field

from polymarket.client import PolymarketClient
from risk.engine import RiskEngine
from signals.engine import SignalEngine
from telegram.auth import TelegramAuth
from telegram.commands import CommandHandler


@dataclass
class TelegramBot:
    auth: TelegramAuth
    risk: RiskEngine
    polymarket: PolymarketClient = field(default_factory=PolymarketClient.from_env)
    signals: SignalEngine = field(init=False)

    def __post_init__(self) -> None:
        # Create SignalEngine with polymarket client for live data
        self.signals = SignalEngine(polymarket=self.polymarket)
        self.handler = CommandHandler(self.auth, self.risk, self.signals, polymarket=self.polymarket)

    def handle_message(self, user_id: int, text: str) -> str:
        response = self.handler.handle(user_id, text)
        return response.text
