from __future__ import annotations

from app.config import load_config
from app.logging import configure_logging
from execution.engine import ExecutionEngine
from risk.engine import RiskEngine
from signals.engine import SignalEngine
from telegram.auth import TelegramAuth
from telegram.bot import TelegramBot


def build_app() -> TelegramBot:
    config = load_config()
    configure_logging()
    # TODO: Wire polymarket.client.PolymarketClient when API integration is complete
    risk = RiskEngine()
    signals = SignalEngine()
    auth = TelegramAuth(admin_ids=set(config.telegram_admins))
    bot = TelegramBot(auth=auth, risk=risk, signals=signals)
    execution = ExecutionEngine()
    execution.set_paper(config.paper_trading)
    return bot


if __name__ == "__main__":
    bot = build_app()
    print(bot.handle_message(0, "/status"))
