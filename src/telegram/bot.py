from __future__ import annotations

from dataclasses import dataclass

from polymarket.client import PolymarketClient
from risk.engine import RiskEngine
from signals.engine import SignalEngine
from telegram.auth import TelegramAuth
from telegram.commands import CommandHandler


@dataclass
class TelegramBot:
    auth: TelegramAuth
    risk: RiskEngine
    signals: SignalEngine
    client: PolymarketClient

    def __post_init__(self) -> None:
        self.handler = CommandHandler(self.auth, self.risk, self.signals, self.client)

    def handle_message(self, user_id: int, text: str) -> str:
        response = self.handler.handle(user_id, text)
        return response.text
