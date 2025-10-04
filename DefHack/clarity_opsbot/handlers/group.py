"""Handlers for group chat interactions."""

from __future__ import annotations

import io
import logging
from datetime import timezone
from typing import Any, Dict, List, Optional, Sequence, Union

from telegram import Update
from telegram.ext import CommandHandler, ContextTypes, MessageHandler, filters

from ..services.gemini import GeminiAnalyzer
from ..services.map_manager import MapManager
from ..services.speech import SpeechTranscriber
from ..utils import format_log, get_observer_signature, get_unit, to_mgrs, utc_iso


def create_group_handlers(
    analyzer: GeminiAnalyzer,
    logger: logging.Logger,
    transcriber: Optional[SpeechTranscriber] = None,
    *,
    map_manager: Optional[MapManager] = None,
) -> List[Union[MessageHandler, CommandHandler]]:
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
        if map_manager:
            tags: Sequence[str] = ("human", "voice") if source == "voice" else ("human", "text")
            await map_manager.add_observation(
                chat_id=chat.id,
                source_id=f"msg-{msg.message_id}",
                lat=None,
                lon=None,
                text=text,
                what=text,
                amount=None,
                observed_at=msg.date,
                unit=unit,
                observer=observer,
                source_type="voice" if source == "voice" else "text",
                tags=tags,
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
        if map_manager:
            accuracy_val = getattr(loc, "horizontal_accuracy", None)
            confidence = 90.0
            if accuracy_val:
                confidence = max(40.0, 100.0 - min(accuracy_val / 5.0, 60.0))
            await map_manager.add_observation(
                chat_id=chat.id,
                source_id=f"loc-{msg.message_id}",
                lat=loc.latitude,
                lon=loc.longitude,
                text="Location update",
                what="Location update",
                amount=None,
                observed_at=msg.date,
                unit=unit,
                observer=observer,
                source_type="sensor",
                confidence=confidence,
                accuracy_m=accuracy_val,
                tags=("friendly", "location"),
                mgrs=mgrs_str,
            )

    async def on_group_map(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        msg = update.effective_message
        if not msg or map_manager is None:
            if msg:
                await msg.reply_text("Map feature is not configured for this deployment.")
            return
        chat = update.effective_chat
        if chat.type not in ("group", "supergroup"):
            return

        raw_args: Sequence[str] = context.args if hasattr(context, "args") else []
        if not raw_args:
            result = await map_manager.render_snapshot(chat.id)
            if not result:
                await msg.reply_text("No recent observations to plot.")
                return
            caption = map_manager.build_caption(result)
            await msg.reply_photo(result.image_bytes, caption=caption)
            return

        subcommand = raw_args[0].lower()
        remaining_raw = list(raw_args[1:])
        remaining_lower = [token.lower() for token in remaining_raw]

        if subcommand == "help":
            await msg.reply_text(
                "Map commands:\n"
                " /map — snapshot\n"
                " /map live [interval] — start live updates\n"
                " /map stop — stop live updates\n"
                " /map focus <term|clear> — filter by term or priority (e.g. P1)\n"
                " /map layers <list> — choose layers (text voices sensors fused alerts)\n"
                " /map diff — highlight changes since last snapshot"
            )
            return

        if subcommand == "live":
            interval = None
            if remaining_raw:
                try:
                    interval = max(120, int(remaining_raw[0]))
                except ValueError:
                    interval = None
            job_queue = getattr(context, "job_queue", None)
            if job_queue is None:
                await msg.reply_text("Job queue unavailable; cannot start live updates.")
                return
            started = await map_manager.start_live(chat.id, job_queue=job_queue, interval=interval)
            if not started:
                await msg.reply_text("Live map updates already running. Use /map stop to end them.")
            else:
                await msg.reply_text("Live map updates activated.")
            return

        if subcommand == "stop":
            job_queue = getattr(context, "job_queue", None)
            if job_queue is None:
                await msg.reply_text("Job queue unavailable; nothing to stop.")
                return
            stopped = await map_manager.stop_live(chat.id, job_queue=job_queue)
            if stopped:
                await msg.reply_text("Live map updates stopped.")
            else:
                await msg.reply_text("Live map updates were not running.")
            return

        if subcommand == "focus":
            if not remaining_raw:
                prefs = map_manager.get_preferences(chat.id)
                if prefs.focus_terms:
                    await msg.reply_text(f"Current focus terms: {' '.join(prefs.focus_terms)}")
                else:
                    await msg.reply_text("No focus terms set.")
                return
            if remaining_lower[0] in {"clear", "none", "reset"}:
                prefs = await map_manager.clear_focus(chat.id)
                await msg.reply_text("Focus cleared.")
            else:
                prefs = await map_manager.set_focus(chat.id, remaining_raw)
                await msg.reply_text(f"Focus set to: {' '.join(prefs.focus_terms)}")
            result = await map_manager.render_snapshot(chat.id)
            if result:
                caption = map_manager.build_caption(result)
                await msg.reply_photo(result.image_bytes, caption=caption)
            else:
                await msg.reply_text("No observations match the current focus.")
            return

        if subcommand == "layers":
            if not remaining_raw:
                prefs = map_manager.get_preferences(chat.id)
                await msg.reply_text(
                    "Active layers: " + ", ".join(sorted(prefs.active_layers))
                )
                return
            prefs = await map_manager.set_layers(chat.id, remaining_lower)
            await msg.reply_text(
                "Layers updated to: " + ", ".join(sorted(prefs.active_layers))
            )
            result = await map_manager.render_snapshot(chat.id)
            if result:
                caption = map_manager.build_caption(result)
                await msg.reply_photo(result.image_bytes, caption=caption)
            else:
                await msg.reply_text("No observations match the selected layers.")
            return

        if subcommand == "diff":
            result = await map_manager.render_snapshot(chat.id, diff=True)
            if not result:
                await msg.reply_text("No observations available to diff.")
                return
            caption = map_manager.build_caption(result)
            await msg.reply_photo(result.image_bytes, caption=caption)
            return

        # fallback: treat as lookback minutes
        try:
            minutes = int(subcommand)
        except ValueError:
            await msg.reply_text("Unknown /map command variant. Use /map help for options.")
            return

        result = await map_manager.render_snapshot(chat.id, lookback_minutes=minutes)
        if not result:
            await msg.reply_text(f"No observations in the last {minutes} minutes.")
            return
        caption = map_manager.build_caption(result)
        await msg.reply_photo(result.image_bytes, caption=caption)

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
        CommandHandler(
            "map",
            on_group_map,
            filters=filters.ChatType.GROUPS,
        ),
    ]
