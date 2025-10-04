"""Application builder for the Clarity Opsbot."""

from __future__ import annotations

import logging
from typing import Optional

from telegram import Update
from telegram.ext import (
    Application,
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    filters,
)

from .config import TELEGRAM_BOT_TOKEN, configure_logging
from .handlers import create_direct_handlers, create_group_handlers
from .observation_repository import ObservationRepository
from .services import FragoGenerator, MapManager
from .services.openai_analyzer import OpenAIAnalyzer


async def _start_group(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Monitoring active")


async def _help_group(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "/start - status\n"
        "This bot captures group text messages and shared locations for analysis and FRAGO support."
    )


def build_app(token: Optional[str] = None) -> Application:
    """Create the Telegram application with configured handlers."""
    logger = configure_logging()
    auth_token = token or TELEGRAM_BOT_TOKEN
    if not auth_token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is not set.")

    app = ApplicationBuilder().token(auth_token).build()

    analyzer = OpenAIAnalyzer(logger)
    analyzer.set_application(app)
    map_manager = MapManager(logger)

    observation_repo = ObservationRepository()
    frago_generator = FragoGenerator(observation_repo)

    for handler in create_group_handlers(analyzer, logger, map_manager=map_manager):
        app.add_handler(handler)
    app.add_handler(CommandHandler("start", _start_group, filters=filters.ChatType.GROUPS))
    app.add_handler(CommandHandler("help", _help_group, filters=filters.ChatType.GROUPS))

    for handler in create_direct_handlers(frago_generator, logger):
        app.add_handler(handler)

    return app


def main() -> None:
    app = build_app()
    logging.getLogger("clarity-opsbot").info("Starting Clarity Opsbot (polling).")
    app.run_polling(close_loop=False)


__all__ = ["build_app", "main"]
