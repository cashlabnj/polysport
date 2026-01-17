from __future__ import annotations

from dataclasses import dataclass
import logging
import os


@dataclass
class AppConfig:
    env: str
    paper_trading: bool
    telegram_admins: list[int]
    db_path: str


def load_config() -> AppConfig:
    env = os.getenv("APP_ENV", "local")
    paper_trading = os.getenv("PAPER_TRADING", "true").lower() == "true"
    admins_raw = os.getenv("TELEGRAM_ADMINS", "")
    admins = [int(value) for value in admins_raw.split(",") if value.strip().isdigit()]
    if not admins:
        logging.getLogger(__name__).warning("telegram_admins_not_configured")
    db_path = os.getenv("DB_PATH", "data/polysport.db")
    return AppConfig(env=env, paper_trading=paper_trading, telegram_admins=admins, db_path=db_path)
