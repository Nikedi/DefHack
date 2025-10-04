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

try:
    import utm  # type: ignore
except ImportError:  # pragma: no cover - fallback dependency
    utm = None

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
    """Convert latitude/longitude to MGRS format string using proper MGRS library.
    
    Example usage from mgrs library:
    >>> import mgrs
    >>> m = mgrs.MGRS()
    >>> c = m.toMGRS(42.0, -93.0)
    >>> c
    '15TWG0000049776'
    """
    # Use the proper MGRS library - this is the authoritative conversion
    if mgrs is not None and _MGRS is not None:
        try:
            # Convert to MGRS using the standard precision (default)
            # The library handles precision automatically
            mgrs_coordinate = _MGRS.toMGRS(lat, lon)
            
            # Handle bytes return (if applicable)
            if isinstance(mgrs_coordinate, bytes):
                mgrs_coordinate = mgrs_coordinate.decode("utf-8")
            
            # Return the MGRS coordinate as-is (library returns proper format)
            return mgrs_coordinate.strip().upper()
            
        except Exception as e:
            # Log the error with more detail
            print(f"⚠️ MGRS conversion failed for lat={lat}, lon={lon}: {e}")
            return "UNKNOWN"
    
    # If MGRS library is not available, return UNKNOWN
    if mgrs is None:
        print("⚠️ MGRS library not available - install with: pip install mgrs")
    elif _MGRS is None:
        print("⚠️ MGRS instance not created properly")
    
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
