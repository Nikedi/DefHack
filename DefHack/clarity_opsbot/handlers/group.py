"""Handlers for group chat interactions."""

from __future__ import annotations

import logging
from datetime import timezone
from typing import Any, Dict, List

from telegram import Update
from telegram.ext import ContextTypes, MessageHandler, filters

from ..services.openai_analyzer import OpenAIAnalyzer
from ..utils import format_log, get_observer_signature, get_unit, to_mgrs, utc_iso


def create_group_handlers(analyzer: OpenAIAnalyzer, logger: logging.Logger) -> List[MessageHandler]:
    async def on_group_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        msg = update.effective_message
        if not msg or not msg.text or msg.from_user is None or msg.from_user.is_bot:
            return
        chat = update.effective_chat
        if chat.type not in ("group", "supergroup"):
            return

        record: Dict[str, str] = {
            "time": utc_iso(),
            "user": msg.from_user.full_name,
            "text": msg.text.replace("\n", " ").strip(),
        }
        logger.info(format_log(record))
        unit = get_unit(chat)
        observer = get_observer_signature(msg.from_user)
        await analyzer.queue_for_analysis(
            chat.id,
            {
                "time": msg.date.astimezone(timezone.utc).isoformat(),
                "unit": unit,
                "observer_signature": observer,
                "mgrs": "UNKNOWN",
                "content": record["text"],
            },
        )

    async def on_group_location(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        msg = update.effective_message
        if not msg or not msg.location or msg.from_user is None or msg.from_user.is_bot:
            return
        chat = update.effective_chat
        if chat.type not in ("group", "supergroup"):
            return
        loc = msg.location
        mgrs_str = to_mgrs(loc.latitude, loc.longitude)
        meta_parts = []
        if getattr(loc, "horizontal_accuracy", None):
            meta_parts.append(f"acc={int(loc.horizontal_accuracy)}m")
        if getattr(loc, "live_period", None):
            meta_parts.append(f"live={loc.live_period}s")
        if getattr(loc, "heading", None):
            meta_parts.append(f"heading={loc.heading}")
        if getattr(loc, "proximity_alert_radius", None):
            meta_parts.append(f"alert_radius={loc.proximity_alert_radius}m")
        meta = (" " + " ".join(meta_parts)) if meta_parts else ""
        logger.info(
            "[%s] user='%s' location=(%.6f,%.6f) mgrs=%s%s",
            utc_iso(),
            msg.from_user.full_name,
            loc.latitude,
            loc.longitude,
            mgrs_str,
            meta,
        )
        unit = get_unit(chat)
        observer = get_observer_signature(msg.from_user)
        await analyzer.queue_for_analysis(
            chat.id,
            {
                "time": msg.date.astimezone(timezone.utc).isoformat(),
                "unit": unit,
                "observer_signature": observer,
                "mgrs": mgrs_str,
                "content": "Location update",
            },
        )

    return [
        MessageHandler(
            filters.ChatType.GROUPS & filters.TEXT & ~filters.COMMAND,
            on_group_text,
        ),
        MessageHandler(
            filters.ChatType.GROUPS & filters.LOCATION,
            on_group_location,
        ),
    ]
