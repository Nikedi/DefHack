"""Utility helpers shared across the Clarity Opsbot components."""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

try:
    import mgrs  # type: ignore
except ImportError:  # pragma: no cover - optional dependency
    mgrs = None

_MGRS = mgrs.MGRS() if mgrs else None


def utc_iso() -> str:
    """Return the current UTC timestamp in ISO-8601 format (seconds precision)."""
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
    except Exception:  # pragma: no cover - defensive fallback
        return "UNKNOWN"


def get_unit(chat) -> str:
    return chat.title or getattr(chat, "username", None) or str(chat.id)


def get_observer_signature(user) -> str:
    return user.username or user.full_name or "UnknownObserver"


def extract_json_payload(text: str) -> Optional[List[Dict[str, Any]]]:
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
