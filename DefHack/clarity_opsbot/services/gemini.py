"""Gemini integration and batching logic."""

from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, Dict, Iterable, List, Optional, Sequence

from ..config import BATCH_WINDOW_SECONDS, GEMINI_API_KEY, GEMINI_MODEL_NAME
from ..models import SensorReading
from ..utils import extract_json_payload

if TYPE_CHECKING:  # pragma: no cover - type checking only
    from .map_manager import MapManager

try:  # pragma: no cover - optional dependency
    from google import generativeai as genai  # type: ignore[attr-defined]
except ImportError:  # pragma: no cover - optional dependency
    genai = None

if GEMINI_API_KEY and genai is not None:  # pragma: no cover - optional dependency
    genai.configure(api_key=GEMINI_API_KEY)


@dataclass(slots=True)
class ChatBatch:
    messages: List[Dict[str, Any]]
    task: Optional[asyncio.Task]


class GeminiAnalyzer:
    """Handle batching of chat messages and enrichment via Gemini."""

    def __init__(self, logger: logging.Logger) -> None:
        self._logger = logger
        self._pending_batches: Dict[int, ChatBatch] = {}
        self._batch_lock = asyncio.Lock()
        self._application = None
        self._gemini_model = self._build_model()
        self._map_manager = None

    def _build_model(self):  # pragma: no cover - external dependency
        if GEMINI_API_KEY and genai is not None:
            try:
                return genai.GenerativeModel(GEMINI_MODEL_NAME)
            except Exception:
                self._logger.exception("Failed to initialise Gemini model")
        elif not GEMINI_API_KEY:
            self._logger.warning("GEMINI_API_KEY not set; Gemini analysis disabled.")
        elif genai is None:
            self._logger.warning("google-generativeai package missing; Gemini analysis disabled.")
        return None

    def set_application(self, application) -> None:
        """Associate the Telegram application for callbacks."""
        self._application = application

    def set_map_manager(self, map_manager: Optional["MapManager"]) -> None:
        """Attach a MapManager to mirror fused observations onto the tactical map."""
        self._map_manager = map_manager

    async def queue_for_analysis(self, chat_id: int, message: Dict[str, Any]) -> None:
        if self._gemini_model is None:
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
        try:
            await asyncio.sleep(BATCH_WINDOW_SECONDS)
        except asyncio.CancelledError:
            return
        await self._flush_chat_batch(chat_id)

    async def _flush_chat_batch(self, chat_id: int) -> None:
        async with self._batch_lock:
            entry = self._pending_batches.pop(chat_id, None)
        if not entry or not entry.messages:
            return
        observations = await self.analyze_with_gemini(entry.messages)
        if not observations:
            return
        if self._map_manager:
            await self._record_map_observations(chat_id, observations)
        payload = self._serialise_observations(observations)
        self._logger.debug("Gemini observations for chat %s: %s", chat_id, payload)
        if self._application:
            try:  # pragma: no cover - requires Telegram runtime
                await self._application.bot.send_message(chat_id=chat_id, text=payload)
            except Exception:  # pragma: no cover - network I/O
                self._logger.exception("Failed sending observations to chat %s", chat_id)

    async def analyze_with_gemini(self, messages: Sequence[Dict[str, Any]]) -> List[SensorReading]:
        if self._gemini_model is None:
            return []
        prompt = self._build_prompt(messages)
        try:  # pragma: no cover - network call
            response = await asyncio.to_thread(self._gemini_model.generate_content, prompt)
        except Exception:  # pragma: no cover - network call
            self._logger.exception("Gemini request failed.")
            return []
        text = getattr(response, "text", "") or ""
        payload = extract_json_payload(text)
        if payload is None:
            self._logger.warning("Gemini response not JSON: %s", text)
            return []
        readings: List[SensorReading] = []
        for item in payload:
            item.setdefault("sensor_id", None)
            reading = self._coerce_sensor_reading(item)
            if reading:
                readings.append(reading)
        return readings

    async def _record_map_observations(
        self,
        chat_id: int,
        observations: Iterable[SensorReading],
    ) -> None:
        if not self._map_manager:
            return
        for reading in observations:
            observed_at = reading.time
            if not isinstance(observed_at, datetime):
                try:
                    observed_at = datetime.fromisoformat(str(observed_at))
                except ValueError:
                    observed_at = datetime.now(timezone.utc)
            if observed_at.tzinfo is None:
                observed_at = observed_at.replace(tzinfo=timezone.utc)
            mgrs_value = getattr(reading, "mgrs", None)
            tags = []
            if reading.unit:
                tags.append(reading.unit)
            if reading.observer_signature:
                tags.append(reading.observer_signature)
            try:
                await self._map_manager.add_observation(
                    chat_id=chat_id,
                    source_id=f"gemini-{reading.observer_signature}-{reading.time.isoformat()}",
                    lat=None,
                    lon=None,
                    text=reading.what,
                    what=reading.what,
                    amount=reading.amount,
                    observed_at=observed_at,
                    unit=reading.unit,
                    observer=reading.observer_signature,
                    source_type="fused",
                    confidence=float(reading.confidence),
                    accuracy_m=None,
                    tags=tags,
                    mgrs=mgrs_value,
                )
            except Exception:  # pragma: no cover - defensive logging
                self._logger.exception("Failed to mirror Gemini observation to map.")

    def _coerce_sensor_reading(self, item: Dict[str, Any]) -> Optional[SensorReading]:
        try:
            reading = SensorReading.model_validate(item)  # type: ignore[attr-defined]
        except AttributeError:  # pragma: no cover - pydantic v1 fallback
            reading = SensorReading.parse_obj(item)  # type: ignore[arg-type]
        except Exception as exc:  # pragma: no cover - validation error
            self._logger.warning("Invalid SensorReading: %s", exc)
            return None
        return reading

    def _serialise_observations(self, observations: Iterable[SensorReading]) -> str:
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
            + "\n\n".join(blocks)
            + "\n\n Examples of output:\n"
            + examples
        )
