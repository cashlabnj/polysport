from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass
class AppConfig:
    env: str
    paper_trading: bool
    telegram_token: str
    telegram_admins: list[int]


def load_config() -> AppConfig:
    env = os.getenv("APP_ENV", "local")
    paper_trading = os.getenv("PAPER_TRADING", "true").lower() == "true"
    telegram_token = os.getenv("TELEGRAM_TOKEN", "")
    admins_raw = os.getenv("TELEGRAM_ADMINS", "")
    admins = [int(value) for value in admins_raw.split(",") if value.strip().isdigit()]
    return AppConfig(
        env=env,
        paper_trading=paper_trading,
        telegram_token=telegram_token,
        telegram_admins=admins,
    )
