"""OpenAI integration and batching logic for DefHack Telegram bot."""

from __future__ import annotations

import asyncio
import json
import logging
import os
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Iterable, List, Optional, Sequence

from ..config import BATCH_WINDOW_SECONDS
from ..models import SensorReading
from ..utils import extract_json_payload

try:
    import openai
except ImportError:
    openai = None

# Get OpenAI API key from environment
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

@dataclass(slots=True)
class ChatBatch:
    messages: List[Dict[str, Any]]
    task: Optional[asyncio.Task]


class OpenAIAnalyzer:
    """Handle batching of chat messages and enrichment via OpenAI."""

    def __init__(self, logger: logging.Logger) -> None:
        self._logger = logger
        self._pending_batches: Dict[int, ChatBatch] = {}
        self._batch_lock = asyncio.Lock()
        self._application = None
        self._openai_client = self._build_client()

    def _build_client(self):
        """Initialize OpenAI client."""
        if OPENAI_API_KEY and openai is not None:
            try:
                return openai.AsyncOpenAI(api_key=OPENAI_API_KEY)
            except Exception:
                self._logger.exception("Failed to initialise OpenAI client")
        elif not OPENAI_API_KEY:
            self._logger.warning("OPENAI_API_KEY not set; OpenAI analysis disabled.")
        elif openai is None:
            self._logger.warning("openai package missing; OpenAI analysis disabled.")
        return None

    def set_application(self, application) -> None:
        """Associate the Telegram application for callbacks."""
        self._application = application

    async def queue_for_analysis(self, chat_id: int, message: Dict[str, Any]) -> None:
        """Queue a message for batch analysis."""
        if self._openai_client is None:
            return
        async with self._batch_lock:
            entry = self._pending_batches.get(chat_id)
            if entry is None:
                entry = ChatBatch(messages=[], task=None)
                self._pending_batches[chat_id] = entry
            entry.messages.append(message)
            if entry.task and not entry.task.done():
                entry.task.cancel()
            entry.task = asyncio.create_task(self._delayed_flush(chat_id))

    async def _delayed_flush(self, chat_id: int) -> None:
        """Wait for batch window then flush messages."""
        try:
            await asyncio.sleep(BATCH_WINDOW_SECONDS)
        except asyncio.CancelledError:
            return
        await self._flush_chat_batch(chat_id)

    async def _flush_chat_batch(self, chat_id: int) -> None:
        """Process accumulated messages for a chat."""
        async with self._batch_lock:
            entry = self._pending_batches.pop(chat_id, None)
        if not entry or not entry.messages:
            return
        
        observations = await self.analyze_with_openai(entry.messages)
        if not observations:
            return
            
        payload = self._serialise_observations(observations)
        self._logger.debug("OpenAI observations for chat %s: %s", chat_id, payload)
        
        if self._application:
            try:
                await self._application.bot.send_message(chat_id=chat_id, text=payload)
            except Exception:
                self._logger.exception("Failed sending observations to chat %s", chat_id)

    async def analyze_with_openai(self, messages: Sequence[Dict[str, Any]]) -> List[SensorReading]:
        """Analyze messages using OpenAI API."""
        if self._openai_client is None:
            return []
            
        prompt = self._build_prompt(messages)
        
        try:
            response = await self._openai_client.chat.completions.create(
                model="gpt-4o-mini",  # Use the same model as DefHack
                messages=[
                    {
                        "role": "system", 
                        "content": "You are a military intelligence analyst converting tactical communications into structured sensor readings. Respond only with valid JSON arrays."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.1,  # Low temperature for consistent structured output
                max_tokens=1000
            )
            
            text = response.choices[0].message.content or ""
            
        except Exception:
            self._logger.exception("OpenAI request failed.")
            return []
            
        payload = extract_json_payload(text)
        if payload is None:
            self._logger.warning("OpenAI response not JSON: %s", text)
            return []
            
        readings: List[SensorReading] = []
        for item in payload:
            item.setdefault("sensor_id", None)
            reading = self._coerce_sensor_reading(item)
            if reading:
                readings.append(reading)
        return readings

    def _coerce_sensor_reading(self, item: Dict[str, Any]) -> Optional[SensorReading]:
        """Convert dictionary to SensorReading model."""
        try:
            reading = SensorReading.model_validate(item)
        except AttributeError:  # pydantic v1 fallback
            reading = SensorReading.parse_obj(item)
        except Exception as exc:
            self._logger.warning("Invalid SensorReading: %s", exc)
            return None
        return reading

    def _serialise_observations(self, observations: Iterable[SensorReading]) -> str:
        """Convert observations to JSON string."""
        obs_list: List[Dict[str, Any]] = []
        for reading in observations:
            data = (
                reading.model_dump() if hasattr(reading, "model_dump") else reading.dict()
            )
            if isinstance(data.get("time"), datetime):
                data["time"] = data["time"].isoformat()
            obs_list.append(data)
        return json.dumps(obs_list, ensure_ascii=False)

    def _build_prompt(self, messages: Sequence[Dict[str, Any]]) -> str:
        """Build analysis prompt for OpenAI."""
        blocks: List[str] = []
        for idx, msg in enumerate(messages, start=1):
            blocks.append(
                f"Message {idx}:\n"
                f"  time: {msg['time']}\n"
                f"  unit: {msg['unit']}\n"
                f"  observer_signature: {msg['observer_signature']}\n"
                f"  mgrs: {msg['mgrs']}\n"
                f"  content: {msg['content']}"
            )
            
        examples = (
            '{"time": "2025-10-03T19:48:41+00:00","mgrs": "35VLG8472571866","what": "Soldier w/ Rifle","amount": 7,"confidence": 90,"sensor_id": null,"unit": "Platoon 1, Squad 2","observer_signature": "JackJames"}'
            "\n"
            '{"time": "2025-10-03T20:37:21+00:00","mgrs": "35VLG8474371854","what": "MT-LB","amount": 2,"confidence": 85,"sensor_id": null,"unit": "Platoon 3, Squad 1","observer_signature": "JimBean"}'
        )
        
        return (
            "You convert tactical chat reports into SensorReading observations for military intelligence.\n"
            "Respond with a JSON array only. Each element must match this schema:\n\n"
            "class SensorReading(BaseModel):\n"
            "    time: datetime  # ISO 8601 UTC format\n"
            "    mgrs: str       # Military Grid Reference System coordinates\n"
            "    what: str       # Description of observed entity/activity\n"
            "    amount: float | None  # Quantity if applicable\n"
            "    confidence: int       # Confidence level 0-100\n"
            "    sensor_id: str | None # Always null for manual observations\n"
            "    unit: str | None      # Military unit designation\n"
            "    observer_signature: str # Observer identification\n\n"
            "Analysis Rules:\n"
            "- Use provided time values exactly (ISO 8601 UTC format)\n"
            "- Use military terminology and standard threat designations\n"
            "- Copy unit and observer_signature exactly as provided\n"
            "- sensor_id MUST always be null for manual observations\n"
            "- mgrs must be uppercase without spaces; use 'UNKNOWN' if location unclear\n"
            "- Combine data from multiple messages into a single observation. Especially when text and location data are available. \n"
            "- Return empty array [] if no actionable intelligence found\n"
            "- Confidence should reflect certainty of observation (confirmed=90+, likely=70-89, possible=40-69)\n\n"
            "Tactical Messages to Analyze:\n"
            + "\n\n".join(blocks)
            + "\n\nExpected JSON Output Format Examples:\n"
            + examples
        )


# Legacy alias for backwards compatibility
GeminiAnalyzer = OpenAIAnalyzer