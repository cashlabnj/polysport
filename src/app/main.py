from __future__ import annotations

import sys

from app.config import load_config
from app.logging import configure_logging
from execution.engine import ExecutionEngine
from risk.engine import RiskEngine
from signals.engine import SignalEngine
from telegram.auth import TelegramAuth
from telegram.bot import TelegramBot
from telegram.runner import TelegramRunner


def main() -> None:
    config = load_config()
    configure_logging()

    if not config.telegram_token:
        print("ERROR: TELEGRAM_TOKEN environment variable is required")
        sys.exit(1)

    # TODO: Wire polymarket.client.PolymarketClient when API integration is complete
    risk = RiskEngine()
    signals = SignalEngine()
    auth = TelegramAuth(admin_ids=set(config.telegram_admins))
    bot = TelegramBot(auth=auth, risk=risk, signals=signals)
    execution = ExecutionEngine()
    execution.set_paper(config.paper_trading)

    # Start the Telegram bot
    runner = TelegramRunner(token=config.telegram_token, bot=bot)
    print(f"Starting bot in {'paper' if config.paper_trading else 'live'} mode...")
    runner.run()


if __name__ == "__main__":
    main()
