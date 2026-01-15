from __future__ import annotations

from risk.engine import RiskEngine
from signals.engine import SignalEngine
from telegram.auth import TelegramAuth
from telegram.commands import CommandHandler


def _handler() -> CommandHandler:
    auth = TelegramAuth(admin_ids={1})
    return CommandHandler(auth=auth, risk=RiskEngine(), signals=SignalEngine())


def test_trade_requires_on_off() -> None:
    handler = _handler()
    response = handler.handle(1, "/trade")
    assert response.text == "usage: /trade on|off"


def test_paper_requires_on_off() -> None:
    handler = _handler()
    response = handler.handle(1, "/paper maybe")
    assert response.text == "usage: /paper on|off"


def test_strategy_requires_enable_disable() -> None:
    handler = _handler()
    response = handler.handle(1, "/strategy toggle vegas")
    assert response.text == "usage: /strategy enable|disable <name>"
