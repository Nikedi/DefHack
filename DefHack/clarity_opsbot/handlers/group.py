"""Handlers for group chat interactions."""

from __future__ import annotations

import io
import logging
from datetime import timezone
from typing import Any, Dict, List, Optional

from telegram import Update
from telegram.ext import ContextTypes, MessageHandler, filters

from ..services.gemini import GeminiAnalyzer
from ..services.speech import SpeechTranscriber
from ..utils import format_log, get_observer_signature, get_unit, to_mgrs, utc_iso


def create_group_handlers(
    analyzer: GeminiAnalyzer,
    logger: logging.Logger,
    transcriber: Optional[SpeechTranscriber] = None,
) -> List[MessageHandler]:
    async def _process_observation(
        chat,
        msg,
        content: str,
        *,
        source: str = "text",
    ) -> None:
        text = (content or "").replace("\n", " ").strip()
        if not text:
            return
        record: Dict[str, str] = {
            "time": utc_iso(),
            "user": msg.from_user.full_name,
            "text": text,
        }
        log_line = format_log(record)
        if source != "text":
            log_line = f"{log_line} (source={source})"
        logger.info(log_line)
        unit = get_unit(chat)
        observer = get_observer_signature(msg.from_user)
        await analyzer.queue_for_analysis(
            chat.id,
            {
                "time": msg.date.astimezone(timezone.utc).isoformat(),
                "unit": unit,
                "observer_signature": observer,
                "mgrs": "UNKNOWN",
                "content": text,
            },
        )

    async def on_group_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        msg = update.effective_message
        if not msg or not msg.text or msg.from_user is None or msg.from_user.is_bot:
            return
        chat = update.effective_chat
        if chat.type not in ("group", "supergroup"):
            return
        await _process_observation(chat, msg, msg.text)

    async def on_group_voice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        msg = update.effective_message
        if not msg or not msg.voice or msg.from_user is None or msg.from_user.is_bot:
            return
        chat = update.effective_chat
        if chat.type not in ("group", "supergroup"):
            return
        if transcriber is None or not transcriber.available:
            logger.warning("Voice message ignored; transcription disabled.")
            await msg.reply_text(
                "Voice transcription isn't configured; please send the observation as text.",
                reply_to_message_id=msg.message_id,
            )
            return

        try:
            voice_file = await context.bot.get_file(msg.voice.file_id)
        except Exception:  # pragma: no cover - network I/O
            logger.exception("Failed to fetch voice file metadata from Telegram.")
            return

        buffer = io.BytesIO()
        try:
            await voice_file.download_to_memory(out=buffer)
        except Exception:  # pragma: no cover - network I/O
            logger.exception("Failed to download voice note for transcription.")
            return

        mime_type = msg.voice.mime_type or "audio/ogg"
        transcript = await transcriber.transcribe(
            buffer.getvalue(),
            filename=f"voice_{msg.voice.file_unique_id}.ogg",
            mime_type=mime_type,
        )
        if not transcript:
            await msg.reply_text(
                "Couldn't transcribe that voice message. Please try again or send text.",
                reply_to_message_id=msg.message_id,
            )
            return

        await msg.reply_text(
            f"Transcribed voice note:\n{transcript}",
            reply_to_message_id=msg.message_id,
        )
        await _process_observation(chat, msg, transcript, source="voice")

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
            filters.ChatType.GROUPS & filters.VOICE,
            on_group_voice,
        ),
        MessageHandler(
            filters.ChatType.GROUPS & filters.LOCATION,
            on_group_location,
        ),
    ]
