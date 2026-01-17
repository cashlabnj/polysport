from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING

from risk.engine import RiskEngine
from signals.engine import SignalEngine
from telegram.auth import TelegramAuth
from telegram.rate_limit import RateLimiter
from telegram.validation import (
    sanitize_log_message,
    validate_market_id,
    validate_numeric_value,
    validate_param_name,
    validate_strategy_name,
)

if TYPE_CHECKING:
    from polymarket.client import PolymarketClient
    from storage.db import Database


@dataclass
class CommandResponse:
    text: str


class CommandHandler:
    def __init__(
        self,
        auth: TelegramAuth,
        risk: RiskEngine,
        signals: SignalEngine,
        db: Database | None = None,
        polymarket: PolymarketClient | None = None,
    ) -> None:
        self.auth = auth
        self.risk = risk
        self.signals = signals
        self.db = db
        self.polymarket = polymarket
        self.paper = True
        self.strategy_state: dict[str, bool] = {}
        self.logger = logging.getLogger(__name__)
        self.watchlist: set[str] = set()
        self.rate_limiter = RateLimiter(max_requests=30, window_seconds=60)

        # Load persisted state if database available
        if self.db:
            self._load_persisted_state()

    def _load_persisted_state(self) -> None:
        """Load state from database on startup."""
        if not self.db:
            return
        self.paper = self.db.get_paper_mode()
        self.risk.trading_enabled = self.db.get_trading_enabled()
        self.watchlist = self.db.get_watchlist()

    def handle(self, user_id: int, command: str) -> CommandResponse:
        # Rate limiting check
        if not self.rate_limiter.is_allowed(user_id):
            self.logger.warning(
                "rate_limit_exceeded",
                extra={"user_id": user_id},
            )
            return CommandResponse(text="Rate limit exceeded. Please wait.")

        # Sanitize command for logging
        safe_command = sanitize_log_message(command)
        self.logger.info(
            "telegram_command_received",
            extra={"user_id": user_id, "command": safe_command},
        )

        if command.startswith("/trade"):
            return self._toggle_trade(user_id, command)
        if command.startswith("/paper"):
            return self._toggle_paper(user_id, command)
        if command.startswith("/strategies"):
            return self._list_strategies()
        if command.startswith("/strategy"):
            return self._toggle_strategy(user_id, command)
        if command.startswith("/markets"):
            return self._get_markets()
        if command.startswith("/watchlist"):
            return self._handle_watchlist(user_id, command)
        if command.startswith("/risk"):
            return self._handle_risk(user_id, command)
        if command.startswith("/orders"):
            return self._get_orders()
        if command.startswith("/wallets"):
            return CommandResponse(text="wallets top: not yet wired")
        if command.startswith("/signals"):
            batch = self.signals.evaluate()
            return CommandResponse(text=f"signals: {len(batch.signals)} active")
        if command.startswith("/status"):
            return self._get_status()
        if command.startswith("/help"):
            return self._get_help()
        return CommandResponse(text="unknown command. Use /help for available commands.")

    def _get_status(self) -> CommandResponse:
        """Get current system status."""
        status = "on" if self.risk.trading_enabled else "off"
        paper_status = "on" if self.paper else "off"
        open_positions = self.db.count_open_positions() if self.db else 0
        daily_pnl = self.db.get_daily_pnl() if self.db else 0.0
        return CommandResponse(
            text=f"status: trading {status}, paper {paper_status}, "
            f"positions {open_positions}, daily_pnl ${daily_pnl:.2f}"
        )

    def _get_orders(self) -> CommandResponse:
        """Get open orders."""
        if not self.db:
            return CommandResponse(text="orders: no open orders")
        orders = self.db.get_open_orders()
        if not orders:
            return CommandResponse(text="orders: no open orders")
        order_lines = [f"  {o['order_id']}: {o['side']} {o['size']}@{o['price']}" for o in orders[:5]]
        return CommandResponse(text=f"orders ({len(orders)} open):\n" + "\n".join(order_lines))

    def _get_markets(self) -> CommandResponse:
        """Get live markets from Polymarket."""
        if not self.polymarket:
            return CommandResponse(text="markets: API not configured")

        try:
            markets = self.polymarket.get_sports_markets(limit=5)
            if not markets:
                return CommandResponse(text="markets: no active sports markets found")

            lines = ["Live Sports Markets:"]
            for market in markets[:5]:
                question = market.question[:60] + "..." if len(market.question) > 60 else market.question
                if market.outcomes:
                    prices = ", ".join(
                        f"{o.name}: {o.price:.0%}" for o in market.outcomes[:2]
                    )
                    lines.append(f"  {question}\n    {prices}")
                else:
                    lines.append(f"  {question}")
            return CommandResponse(text="\n".join(lines))
        except Exception as e:
            self.logger.error(f"Failed to fetch markets: {e}")
            return CommandResponse(text="markets: failed to fetch (API error)")

    def _list_strategies(self) -> CommandResponse:
        """List all available strategies with their status."""
        lines = ["Available strategies:"]
        for strategy in self.signals.strategies:
            name = strategy.__class__.__name__
            # Check if strategy is enabled (default: enabled)
            enabled = self.strategy_state.get(name, True)
            status = "ON" if enabled else "OFF"
            lines.append(f"  {name}: {status}")
        return CommandResponse(text="\n".join(lines))

    def _get_help(self) -> CommandResponse:
        """Get help message."""
        return CommandResponse(
            text=(
                "Available commands:\n"
                "/status - Show system status\n"
                "/signals - Show active signals\n"
                "/strategies - List all strategies\n"
                "/orders - Show open orders\n"
                "/markets - Show available markets\n"
                "/trade on|off - Enable/disable trading (admin)\n"
                "/paper on|off - Enable/disable paper mode (admin)\n"
                "/strategy enable|disable <name> - Toggle strategy (admin)\n"
                "/watchlist add|remove <market_id> - Manage watchlist (admin)\n"
                "/risk set <param> <value> - Set risk parameter (admin)"
            )
        )

    def _toggle_trade(self, user_id: int, command: str) -> CommandResponse:
        if not self.auth.is_admin(user_id):
            self.logger.warning(
                "telegram_command_denied",
                extra={"user_id": user_id, "command": "trade"},
            )
            return CommandResponse(text="unauthorized")

        enabled = self._parse_toggle(command)
        if enabled is None:
            return CommandResponse(text="usage: /trade on|off")

        self.risk.set_trading(enabled)

        # Persist to database
        if self.db:
            self.db.set_trading_enabled(enabled)
            self.db.log_action(
                actor_id=str(user_id),
                action="trade_toggle",
                details=f"enabled={enabled}",
            )

        self.logger.info("trade_toggle", extra={"user_id": user_id, "enabled": enabled})
        return CommandResponse(text=f"trade {'on' if enabled else 'off'}")

    def _toggle_paper(self, user_id: int, command: str) -> CommandResponse:
        if not self.auth.is_admin(user_id):
            self.logger.warning(
                "telegram_command_denied",
                extra={"user_id": user_id, "command": "paper"},
            )
            return CommandResponse(text="unauthorized")

        enabled = self._parse_toggle(command)
        if enabled is None:
            return CommandResponse(text="usage: /paper on|off")

        self.paper = enabled

        # Persist to database
        if self.db:
            self.db.set_paper_mode(enabled)
            self.db.log_action(
                actor_id=str(user_id),
                action="paper_toggle",
                details=f"enabled={enabled}",
            )

        self.logger.info("paper_toggle", extra={"user_id": user_id, "enabled": self.paper})
        return CommandResponse(text=f"paper {'on' if self.paper else 'off'}")

    def _toggle_strategy(self, user_id: int, command: str) -> CommandResponse:
        if not self.auth.is_admin(user_id):
            self.logger.warning(
                "telegram_command_denied",
                extra={"user_id": user_id, "command": "strategy"},
            )
            return CommandResponse(text="unauthorized")

        parts = command.split()
        if len(parts) < 3:
            return CommandResponse(text="usage: /strategy enable|disable <name>")

        action, name = parts[1], parts[2]

        # Validate inputs
        if action not in {"enable", "disable"}:
            return CommandResponse(text="usage: /strategy enable|disable <name>")
        if not validate_strategy_name(name):
            return CommandResponse(text="Invalid strategy name")

        enabled = action == "enable"
        self.strategy_state[name] = enabled

        # Persist to database
        if self.db:
            self.db.set_strategy_enabled(name, enabled)
            self.db.log_action(
                actor_id=str(user_id),
                action="strategy_toggle",
                details=f"strategy={name}, enabled={enabled}",
            )

        self.logger.info(
            "strategy_toggle",
            extra={"user_id": user_id, "strategy": name, "enabled": enabled},
        )
        return CommandResponse(text=f"strategy {name} {'enabled' if enabled else 'disabled'}")

    def _handle_watchlist(self, user_id: int, command: str) -> CommandResponse:
        if not self.auth.is_admin(user_id):
            self.logger.warning(
                "telegram_command_denied",
                extra={"user_id": user_id, "command": "watchlist"},
            )
            return CommandResponse(text="unauthorized")

        parts = command.split()
        if len(parts) < 3:
            return CommandResponse(text="usage: /watchlist add|remove <market_id>")

        action, market_id = parts[1], parts[2]

        # Validate market_id
        if not validate_market_id(market_id):
            return CommandResponse(text="Invalid market ID")

        if action == "add":
            self.watchlist.add(market_id)
            if self.db:
                self.db.add_to_watchlist(market_id)
        elif action == "remove":
            self.watchlist.discard(market_id)
            if self.db:
                self.db.remove_from_watchlist(market_id)
        else:
            return CommandResponse(text="usage: /watchlist add|remove <market_id>")

        if self.db:
            self.db.log_action(
                actor_id=str(user_id),
                action="watchlist_update",
                details=f"action={action}, market_id={market_id}",
            )

        self.logger.info(
            "watchlist_update",
            extra={"user_id": user_id, "action": action, "market_id": market_id},
        )
        return CommandResponse(text=f"watchlist {action} {market_id}")

    def _handle_risk(self, user_id: int, command: str) -> CommandResponse:
        if not self.auth.is_admin(user_id):
            self.logger.warning(
                "telegram_command_denied",
                extra={"user_id": user_id, "command": "risk"},
            )
            return CommandResponse(text="unauthorized")

        parts = command.split()
        if len(parts) < 4 or parts[1] != "set":
            return CommandResponse(text="usage: /risk set <param> <value>")

        param, raw_value = parts[2], parts[3]

        # Validate param name
        if not validate_param_name(param):
            return CommandResponse(text="Invalid parameter name")

        # Validate numeric value
        value = validate_numeric_value(raw_value, min_val=0.0, max_val=1e9)
        if value is None:
            return CommandResponse(text="Invalid value (must be number >= 0)")

        updated = self.risk.set_limit(param, value)
        if not updated:
            return CommandResponse(text=f"risk param {param} not recognized or invalid")

        if self.db:
            self.db.log_action(
                actor_id=str(user_id),
                action="risk_param_set",
                details=f"param={param}, value={value}",
            )

        self.logger.info(
            "risk_param_set",
            extra={"user_id": user_id, "param": param, "value": value},
        )
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
