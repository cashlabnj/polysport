from __future__ import annotations

from dataclasses import dataclass
import logging
from typing import Dict

from risk.engine import RiskEngine
from signals.engine import SignalEngine
from telegram.auth import TelegramAuth


@dataclass
class CommandResponse:
    text: str


class CommandHandler:
    def __init__(self, auth: TelegramAuth, risk: RiskEngine, signals: SignalEngine) -> None:
        self.auth = auth
        self.risk = risk
        self.signals = signals
        self.paper = True
        self.strategy_state: Dict[str, bool] = {}
        self.logger = logging.getLogger(__name__)
        self.watchlist: set[str] = set()

    def handle(self, user_id: int, command: str) -> CommandResponse:
        self.logger.info("telegram_command_received", extra={"user_id": user_id, "command": command})
        if command.startswith("/trade"):
            return self._toggle_trade(user_id, command)
        if command.startswith("/paper"):
            return self._toggle_paper(user_id, command)
        if command.startswith("/strategy"):
            return self._toggle_strategy(user_id, command)
        if command.startswith("/markets"):
            return CommandResponse(text="markets: demo-market")
        if command.startswith("/watchlist"):
            return self._handle_watchlist(user_id, command)
        if command.startswith("/risk"):
            return self._handle_risk(user_id, command)
        if command.startswith("/orders"):
            return CommandResponse(text="orders: no open orders")
        if command.startswith("/wallets"):
            return CommandResponse(text="wallets top: not yet wired")
        if command.startswith("/signals"):
            batch = self.signals.evaluate()
            return CommandResponse(text=f"signals: {len(batch.signals)} active")
        if command.startswith("/status"):
            status = "on" if self.risk.trading_enabled else "off"
            return CommandResponse(text=f"status: trading {status}, paper {self.paper}")
        return CommandResponse(text="unknown command")

    def _toggle_trade(self, user_id: int, command: str) -> CommandResponse:
        if not self.auth.is_admin(user_id):
            self.logger.warning("telegram_command_denied", extra={"user_id": user_id, "command": command})
            return CommandResponse(text="unauthorized")
        enabled = self._parse_toggle(command)
        if enabled is None:
            return CommandResponse(text="usage: /trade on|off")
        self.risk.set_trading(enabled)
        self.logger.info("trade_toggle", extra={"user_id": user_id, "enabled": enabled})
        return CommandResponse(text=f"trade {'on' if enabled else 'off'}")

    def _toggle_paper(self, user_id: int, command: str) -> CommandResponse:
        if not self.auth.is_admin(user_id):
            self.logger.warning("telegram_command_denied", extra={"user_id": user_id, "command": command})
            return CommandResponse(text="unauthorized")
        enabled = self._parse_toggle(command)
        if enabled is None:
            return CommandResponse(text="usage: /paper on|off")
        self.paper = enabled
        self.logger.info("paper_toggle", extra={"user_id": user_id, "enabled": self.paper})
        return CommandResponse(text=f"paper {'on' if self.paper else 'off'}")

    def _toggle_strategy(self, user_id: int, command: str) -> CommandResponse:
        if not self.auth.is_admin(user_id):
            self.logger.warning("telegram_command_denied", extra={"user_id": user_id, "command": command})
            return CommandResponse(text="unauthorized")
        parts = command.split()
        if len(parts) < 3:
            return CommandResponse(text="usage: /strategy enable|disable <name>")
        action, name = parts[1], parts[2]
        if action not in {"enable", "disable"}:
            return CommandResponse(text="usage: /strategy enable|disable <name>")
        self.strategy_state[name] = action == "enable"
        self.logger.info("strategy_toggle", extra={"user_id": user_id, "strategy": name, "enabled": action == "enable"})
        return CommandResponse(text=f"strategy {name} {action}")

    def _handle_watchlist(self, user_id: int, command: str) -> CommandResponse:
        if not self.auth.is_admin(user_id):
            self.logger.warning("telegram_command_denied", extra={"user_id": user_id, "command": command})
            return CommandResponse(text="unauthorized")
        parts = command.split()
        if len(parts) < 3:
            return CommandResponse(text="usage: /watchlist add|remove <market_id>")
        action, market_id = parts[1], parts[2]
        if action == "add":
            self.watchlist.add(market_id)
        elif action == "remove":
            self.watchlist.discard(market_id)
        else:
            return CommandResponse(text="usage: /watchlist add|remove <market_id>")
        self.logger.info("watchlist_update", extra={"user_id": user_id, "action": action, "market_id": market_id})
        return CommandResponse(text=f"watchlist {action} {market_id}")

    def _handle_risk(self, user_id: int, command: str) -> CommandResponse:
        if not self.auth.is_admin(user_id):
            self.logger.warning("telegram_command_denied", extra={"user_id": user_id, "command": command})
            return CommandResponse(text="unauthorized")
        parts = command.split()
        if len(parts) < 4 or parts[1] != "set":
            return CommandResponse(text="usage: /risk set <param> <value>")
        param, raw_value = parts[2], parts[3]
        try:
            value = float(raw_value)
        except ValueError:
            return CommandResponse(text="usage: /risk set <param> <value>")
        updated = self.risk.set_limit(param, value)
        if not updated:
            return CommandResponse(text=f"risk param {param} not recognized or invalid")
        self.logger.info("risk_param_set", extra={"user_id": user_id, "param": param, "value": value})
        return CommandResponse(text=f"risk {param} set to {value}")

    @staticmethod
    def _parse_toggle(command: str) -> bool | None:
        parts = command.split()
        if len(parts) != 2:
            return None
        value = parts[1].lower()
        if value not in {"on", "off"}:
            return None
        return value == "on"
