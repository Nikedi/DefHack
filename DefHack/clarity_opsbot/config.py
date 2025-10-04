"""Configuration helpers for the Clarity Opsbot."""

from __future__ import annotations

import logging
import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
GEMINI_MODEL_NAME = os.environ.get("GEMINI_MODEL_NAME", "gemini-flash-latest")
BATCH_WINDOW_SECONDS = int(os.environ.get("BATCH_WINDOW_SECONDS", "20"))
LOG_LEVEL = os.environ.get("LOG_LEVEL", "WARNING").upper()

LOGGER_NAME = "clarity-opsbot"


def configure_logging() -> logging.Logger:
    """Configure root logging and return the package logger."""
    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL, logging.WARNING),
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )
    return logging.getLogger(LOGGER_NAME)
