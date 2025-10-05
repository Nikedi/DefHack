"""Handlers for direct message conversations with the bot."""

from __future__ import annotations

import logging
from typing import List

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import (
    CommandHandler,
    ConversationHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from ..services.frago import FragoGenerator

ASK_OBJECTIVE, ASK_KEYWORDS = range(2)


def create_direct_handlers(frago_generator: FragoGenerator, logger: logging.Logger):
    async def start_private(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        await update.message.reply_text(
            "Clarity Opsbot ready. Use /frago to generate a FRAGO order from the latest "
            "subordinate observations."
        )

    async def help_private(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        await update.message.reply_text(
            "Commands available in direct messages:\n"
            "/frago - Build a FRAGO order scaffold using the latest observation feeds."
        )

    async def frago_entry(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        context.user_data.clear()
        await update.message.reply_text(
            "Let's prepare a FRAGO. What's your primary objective or mission focus? "
            "Reply with a sentence or type 'skip'."
        )
        return ASK_OBJECTIVE

    async def frago_objective(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        text = (update.message.text or "").strip()
        if text.lower() != "skip":
            context.user_data["objective"] = text
        await update.message.reply_text(
            "Got it. Any keywords or units you want to prioritise? "
            "(Example: 'armor', 'Bravo squad'). Respond with comma-separated words or 'skip'."
        )
        return ASK_KEYWORDS

    async def frago_keywords(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        text = (update.message.text or "").strip()
        keywords: List[str] = []
        if text.lower() != "skip":
            keywords = [token.strip() for token in text.split(",") if token.strip()]
        order = frago_generator.create_order(
            objective=context.user_data.get("objective"),
            keywords=keywords,
        )
        await update.message.reply_text(
            order.to_markdown(),
            parse_mode=ParseMode.MARKDOWN,
        )
        await update.message.reply_text(
            "FRAGO draft complete. You can run /frago again for a new order based on updated inputs."
        )
        return ConversationHandler.END

    async def frago_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        await update.message.reply_text("FRAGO creation cancelled. Use /frago to restart when ready.")
        return ConversationHandler.END

    async def on_private_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        await update.message.reply_text(
            "I'm standing by. Use /frago to build a FRAGO order or /help for available commands."
        )

    conversation = ConversationHandler(
        entry_points=[
            CommandHandler(
                "frago",
                frago_entry,
                filters=filters.ChatType.PRIVATE,
            )
        ],
        states={
            ASK_OBJECTIVE: [MessageHandler(filters.ChatType.PRIVATE & filters.TEXT & ~filters.COMMAND, frago_objective)],
            ASK_KEYWORDS: [MessageHandler(filters.ChatType.PRIVATE & filters.TEXT & ~filters.COMMAND, frago_keywords)],
        },
        fallbacks=[
            CommandHandler("cancel", frago_cancel, filters=filters.ChatType.PRIVATE),
        ],
        allow_reentry=True,
    )

    return [
        CommandHandler("start", start_private, filters=filters.ChatType.PRIVATE),
        CommandHandler("help", help_private, filters=filters.ChatType.PRIVATE),
        conversation,
        MessageHandler(
            filters.ChatType.PRIVATE & filters.TEXT & ~filters.COMMAND,
            on_private_text,
        ),
    ]
