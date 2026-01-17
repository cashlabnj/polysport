from __future__ import annotations

from app.config import load_config
from app.logging import configure_logging
from polymarket.client import PolymarketClient
from risk.engine import RiskEngine
from signals.engine import SignalEngine
from telegram.auth import TelegramAuth
from telegram.bot import TelegramBot
from execution.engine import ExecutionEngine


def build_app() -> TelegramBot:
    config = load_config()
    configure_logging()
    client = PolymarketClient.from_env()
    risk = RiskEngine()
    signals = SignalEngine()
    auth = TelegramAuth(admin_ids=set(config.telegram_admins))
    bot = TelegramBot(auth=auth, risk=risk, signals=signals, client=client)
    execution = ExecutionEngine(db_path=config.db_path)
    execution.set_paper(config.paper_trading)
    return bot


if __name__ == "__main__":
    bot = build_app()
    print(bot.handle_message(0, "/status"))
