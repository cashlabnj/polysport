"""Telegram bot runner using python-telegram-bot library."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from telegram import Update
from telegram.bot import TelegramBot
from telegram.ext import Application, ContextTypes, MessageHandler, filters
from telegram.ext import CommandHandler as TGCommandHandler

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class TelegramRunner:
    """Runs the Telegram bot with actual Telegram API polling."""

    def __init__(self, token: str, bot: TelegramBot) -> None:
        self.token = token
        self.bot = bot
        self.app: Application | None = None

    async def _handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle incoming messages."""
        if update.message is None or update.message.text is None:
            return

        user_id = update.effective_user.id if update.effective_user else 0
        text = update.message.text

        logger.info(f"Received message from {user_id}: {text[:50]}")

        response = self.bot.handle_message(user_id, text)

        if response:
            await update.message.reply_text(response)

    async def _handle_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle slash commands."""
        if update.message is None or update.message.text is None:
            return

        user_id = update.effective_user.id if update.effective_user else 0
        text = update.message.text

        logger.info(f"Received command from {user_id}: {text}")

        response = self.bot.handle_message(user_id, text)

        if response:
            await update.message.reply_text(response)

    def run(self) -> None:
        """Start the bot with polling."""
        self.app = Application.builder().token(self.token).build()

        # Handle all commands
        self.app.add_handler(TGCommandHandler(
            ["start", "help", "status", "trade", "paper", "strategy", "strategies", "limit", "watch", "unwatch", "signals", "orders", "cancel", "markets", "watchlist", "risk", "wallets"],
            self._handle_command
        ))

        # Handle text messages (for any commands we might have missed)
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self._handle_message))

        logger.info("Starting Telegram bot polling...")
        self.app.run_polling(allowed_updates=Update.ALL_TYPES)
