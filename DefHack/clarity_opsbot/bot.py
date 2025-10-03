import os
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
import asyncio
import json
import re
from pydantic import BaseModel, Field, ValidationError

# -------------------------------------------------
# Config
# -------------------------------------------------
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")

logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger("group-monitor")

# MGRS support and Gemini integration
try:
    import mgrs  # pip install mgrs
    _MGRS = mgrs.MGRS()
except ImportError:
    _MGRS = None

try:
    from google import generativeai as genai  # type: ignore[attr-defined]
except ImportError:
    genai = None

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
GEMINI_MODEL_NAME = os.environ.get("GEMINI_MODEL_NAME", "gemini-flash-latest")
_GEMINI_MODEL = None
if GEMINI_API_KEY and genai is not None:
    genai.configure(api_key=GEMINI_API_KEY)
    _GEMINI_MODEL = genai.GenerativeModel(GEMINI_MODEL_NAME)
elif not GEMINI_API_KEY:
    logger.warning("GEMINI_API_KEY not set; Gemini analysis disabled.")
elif genai is None:
    logger.warning("google-generativeai package missing; Gemini analysis disabled.")

BATCH_WINDOW_SECONDS = 20
_pending_batches: Dict[int, Dict[str, Any]] = {}  # chat_id -> {"messages": [...], "task": Task}
_batch_lock = asyncio.Lock()
GLOBAL_APP: Optional[Application] = None  # set in build_app

class SensorReading(BaseModel):
    time: datetime
    mgrs: str = Field(default="UNKNOWN", description="Single MGRS string, uppercase, no spaces")
    what: str
    amount: Optional[float] = None
    confidence: int = Field(ge=0, le=100)
    sensor_id: Optional[str] = None
    unit: Optional[str] = None
    observer_signature: str = Field(min_length=3, description="e.g., 'Sensor 1, Team A'")

# -------------------------------------------------
# Helpers
# -------------------------------------------------
def utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def format_log(record: Dict[str, str]) -> str:
    return (
        f"[{record['time']}]"
        f" user='{record['user']}'"
        f" text={record['text']!r}"
    )

def to_mgrs(lat: float, lon: float) -> str:
    if _MGRS is None:
        return "UNKNOWN"
    try:
        value = _MGRS.toMGRS(lat, lon)
        if isinstance(value, bytes):
            value = value.decode("utf-8")
        return value.replace(" ", "").upper()
    except Exception:
        return "UNKNOWN"

def _get_unit(chat) -> str:
    return chat.title or getattr(chat, "username", None) or str(chat.id)

def _get_observer_signature(user) -> str:
    return user.username or user.full_name or "UnknownObserver"

async def queue_for_analysis(chat_id: int, message: Dict[str, Any]) -> None:
    if _GEMINI_MODEL is None:
        return
    async with _batch_lock:
        entry = _pending_batches.get(chat_id)
        if entry is None:
            entry = {"messages": [], "task": None}
            _pending_batches[chat_id] = entry
        entry["messages"].append(message)
        if entry["task"] and not entry["task"].done():
            entry["task"].cancel()
        entry["task"] = asyncio.create_task(_delayed_flush(chat_id))

async def _delayed_flush(chat_id: int) -> None:
    try:
        await asyncio.sleep(BATCH_WINDOW_SECONDS)
    except asyncio.CancelledError:
        return
    await _flush_chat_batch(chat_id)

async def _flush_chat_batch(chat_id: int) -> None:
    async with _batch_lock:
        entry = _pending_batches.pop(chat_id, None)
    if not entry:
        return
    messages = entry["messages"]
    if not messages:
        return
    observations = await analyze_with_gemini(messages)
    if not observations:
        return
    # Serialize observations to JSON
    obs_list: List[Dict[str, Any]] = []
    for r in observations:
        d = (r.model_dump() if hasattr(r, "model_dump") else r.dict())  # pydantic v2/v1
        # Ensure datetime ISO
        if isinstance(d.get("time"), datetime):
            d["time"] = d["time"].isoformat()
        obs_list.append(d)
    payload = json.dumps(obs_list, ensure_ascii=False)
    print(f"[Gemini->Chat:{chat_id}] {payload}", flush=True)
    if GLOBAL_APP:
        try:
            await GLOBAL_APP.bot.send_message(chat_id=chat_id, text=payload)
        except Exception:
            logger.exception("Failed sending observations to chat %s", chat_id)

async def analyze_with_gemini(messages: List[Dict[str, Any]]) -> List[SensorReading]:
    if _GEMINI_MODEL is None:
        return []
    prompt = _build_gemini_prompt(messages)
    try:
        response = await asyncio.to_thread(_GEMINI_MODEL.generate_content, prompt)
    except Exception:
        logger.exception("Gemini request failed.")
        return []
    text = getattr(response, "text", "") or ""
    payload = _extract_json_payload(text)
    if payload is None:
        logger.warning("Gemini response not JSON: %s", text)
        return []
    readings: List[SensorReading] = []
    for item in payload:
        item.setdefault("sensor_id", None)
        try:
            reading = SensorReading.model_validate(item)  # type: ignore[attr-defined]
        except AttributeError:
            reading = SensorReading.parse_obj(item)  # type: ignore[arg-type]
        except ValidationError as exc:
            logger.warning("Invalid SensorReading: %s", exc)
            continue
        readings.append(reading)
    return readings

def _build_gemini_prompt(messages: List[Dict[str, Any]]) -> str:
    blocks = []
    for idx, msg in enumerate(messages, start=1):
        blocks.append(
            f"Message {idx}:\n"
            f"  time: {msg['time']}\n"
            f"  unit: {msg['unit']}\n"
            f"  observer_signature: {msg['observer_signature']}\n"
            f"  mgrs: {msg['mgrs']}\n"
            f"  content: {msg['content']}"
        )
    return (
        "You convert chat reports into SensorReading observations.\n"
        "Respond with a JSON array only. Each element must match:\n"
        "class SensorReading(BaseModel):\n"
        "    time: datetime\n"
        "    mgrs: str\n"
        "    what: str\n"
        "    amount: float | None\n"
        "    confidence: int\n"
        "    sensor_id: str | None\n"
        "    unit: str | None\n"
        "    observer_signature: str\n"
        "Rules:\n"
        "- Use provided time values (ISO 8601 UTC).\n"
        "- Use military terms and language.\n"
        "- Copy unit and observer_signature exactly.\n"
        "- sensor_id MUST be null.\n"
        "- mgrs must be uppercase without spaces; if unknown use 'UNKNOWN'.\n"
        "- The messages supplied come from the same observation. Combine the data from both to just one observation.\n"
        "- Return [] if nothing actionable.\n"
        "Messages:\n"
        + "\n\n".join(blocks) + "\n\n Examples of output:\n"
        '{"time": "2025-10-03T19:48:41+00:00","mgrs": "35VLG8472571866","what": "Soldier w/ Rifle","amount": 7,"confidence": 90,"sensor_id": null,"unit": "Platoon 1, Squad 2","observer_signature": "JackJames"}\n'
        '{"time": "2025-10-03T20:37:21+00:00","mgrs": "35VLG8474371854","what": "MT-LB","amount": 2,"confidence": 85,"sensor_id": null,"unit": "Platoon 3, Squad 1","observer_signature": "JimBean"}'
    )

def _extract_json_payload(text: str) -> Optional[List[Dict[str, Any]]]:
    text = text.strip()
    if text.startswith("```"):
        fence = text.find("```", 3)
        if fence != -1:
            text = text[3:fence].strip()
            if text.lower().startswith("json"):
                text = text[4:].strip()
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\[[\s\S]*\]", text)
        if not match:
            return None
        try:
            data = json.loads(match.group(0))
        except json.JSONDecodeError:
            return None
    if isinstance(data, dict):
        data = [data]
    return data if isinstance(data, list) else None

# -------------------------------------------------
# Command Handlers
# -------------------------------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Monitoring active"
    )

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "/start - status\n"
        "This bot prints group text messages and shared locations to the terminal."
    )

# -------------------------------------------------
# Message Handler
# -------------------------------------------------
async def on_group_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    msg = update.effective_message
    if not msg or not msg.text or msg.from_user is None or msg.from_user.is_bot:
        return
    chat = update.effective_chat
    if chat.type not in ("group", "supergroup"):
        return

    record = {
        "time": utc_iso(),
        "user": msg.from_user.full_name,
        "text": msg.text.replace("\n", " ").strip(),
    }

    # Print to stdout (terminal)
    print(format_log(record), flush=True)
    unit = _get_unit(chat)
    observer = _get_observer_signature(msg.from_user)
    await queue_for_analysis(
        chat.id,
        {
            "time": msg.date.astimezone(timezone.utc).isoformat(),
            "unit": unit,
            "observer_signature": observer,
            "mgrs": "UNKNOWN",
            "content": record["text"],
        }
    )

# NEW: handler for location messages
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
    print(
        f"[{utc_iso()}] user='{msg.from_user.full_name}' "
        f"location=({loc.latitude:.6f},{loc.longitude:.6f}) mgrs={mgrs_str}{meta}",
        flush=True,
    )
    unit = _get_unit(chat)
    observer = _get_observer_signature(msg.from_user)
    await queue_for_analysis(
        chat.id,
        {
            "time": msg.date.astimezone(timezone.utc).isoformat(),
            "unit": unit,
            "observer_signature": observer,
            "mgrs": mgrs_str,
            "content": "Location update",
        }
    )

# -------------------------------------------------
# App Builder
# -------------------------------------------------
def build_app() -> Application:
    if not TELEGRAM_BOT_TOKEN:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is not set.")
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    #Register text handler
    app.add_handler(
        MessageHandler(
            filters.ChatType.GROUPS & filters.TEXT & ~filters.COMMAND,
            on_group_text,
        )
    )
    # Register location handler
    app.add_handler(
        MessageHandler(
            filters.ChatType.GROUPS & filters.LOCATION,
            on_group_location,
        )
    )
    global GLOBAL_APP
    GLOBAL_APP = app
    return app

def main() -> None:
    app = build_app()
    logger.info("Starting group monitor bot (polling).")
    app.run_polling(close_loop=False)

if __name__ == "__main__":
    main()
