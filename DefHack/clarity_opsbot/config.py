"""Configuration helpers for the Clarity Opsbot."""

from __future__ import annotations

import logging
import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
OPENAI_MODEL_NAME = os.environ.get("OPENAI_MODEL_NAME", "gpt-4o-mini")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")  # Keep for backwards compatibility
GEMINI_MODEL_NAME = os.environ.get("GEMINI_MODEL_NAME", "gemini-flash-latest")
BATCH_WINDOW_SECONDS = int(os.environ.get("BATCH_WINDOW_SECONDS", "20"))

# Map feature configuration (ported from copyDefHack)
MAP_TILE_URL = os.environ.get("MAP_TILE_URL", "https://tile.openstreetmap.org/{z}/{x}/{y}.png")
MAP_WIDTH = int(os.environ.get("MAP_WIDTH", "1024"))
MAP_HEIGHT = int(os.environ.get("MAP_HEIGHT", "768"))
MAP_LOOKBACK_MINUTES = int(os.environ.get("MAP_LOOKBACK_MINUTES", "120"))
MAP_CLUSTER_THRESHOLD_METERS = float(os.environ.get("MAP_CLUSTER_THRESHOLD_METERS", "200"))
MAP_LIVE_INTERVAL_SECONDS = int(os.environ.get("MAP_LIVE_INTERVAL_SECONDS", "420"))
MAP_MAX_POINTS = int(os.environ.get("MAP_MAX_POINTS", "400"))
MAP_AGE_FADE_MINUTES = int(os.environ.get("MAP_AGE_FADE_MINUTES", "60"))
MAP_RECENT_SECONDS = int(os.environ.get("MAP_RECENT_SECONDS", "300"))
MAP_CONFIDENCE_SCALE_METERS = float(os.environ.get("MAP_CONFIDENCE_SCALE_METERS", "15"))

LOG_LEVEL = os.environ.get("LOG_LEVEL", "WARNING").upper()

LOGGER_NAME = "clarity-opsbot"


def configure_logging() -> logging.Logger:
    """Configure root logging and return the package logger."""
    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL, logging.WARNING),
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )
    return logging.getLogger(LOGGER_NAME)
