"""Speech-to-text utilities for handling voice observations."""

from __future__ import annotations

import asyncio
import logging
import os
import tempfile
from typing import Optional

from ..config import GEMINI_API_KEY, GEMINI_TRANSCRIPTION_MODEL

try:  # pragma: no cover - optional dependency
    from google import generativeai as genai  # type: ignore[attr-defined]
except ImportError:  # pragma: no cover - optional dependency
    genai = None  # type: ignore[assignment]


class SpeechTranscriber:
    """Wrap Gemini audio transcription for Telegram voice notes."""

    def __init__(self, logger: logging.Logger) -> None:
        self._logger = logger.getChild("speech")
        self._model_name = GEMINI_TRANSCRIPTION_MODEL
        self._model = self._build_model()

    def _build_model(self):  # pragma: no cover - external dependency
        if not GEMINI_API_KEY:
            self._logger.warning("GEMINI_API_KEY not set; voice transcription disabled.")
            return None
        if genai is None:
            self._logger.warning(
                "google-generativeai package missing; voice transcription disabled."
            )
            return None
        try:
            genai.configure(api_key=GEMINI_API_KEY)
            return genai.GenerativeModel(self._model_name)
        except Exception:
            self._logger.exception("Failed to initialise Gemini transcription model.")
            return None

    @property
    def available(self) -> bool:
        """Return whether transcription is available."""
        return self._model is not None

    async def transcribe(
        self,
        audio_bytes: bytes,
        *,
        filename: str,
        mime_type: str = "audio/ogg",
    ) -> Optional[str]:
        """Run transcription on the provided audio payload."""
        if not self.available:
            return None

        payload = bytes(audio_bytes)

        def _invoke():  # pragma: no cover - network call
            tmp_path: Optional[str] = None
            uploaded = None
            transcript: Optional[str] = None
            try:
                suffix = os.path.splitext(filename)[1] or ".ogg"
                with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
                    tmp_file.write(payload)
                    tmp_path = tmp_file.name

                uploaded = genai.upload_file(
                    path=tmp_path,
                    mime_type=mime_type,
                )

                file_uri = getattr(uploaded, "uri", None)
                if not file_uri:
                    self._logger.warning(
                        "Gemini upload for %s returned no file URI; cannot transcribe.", filename
                    )
                    return None

                prompt = [
                    {
                        "role": "user",
                        "parts": [
                            {"text": "Transcribe this audio message. Return only the transcript text."},
                            {
                                "file_data": {
                                    "mime_type": getattr(uploaded, "mime_type", mime_type),
                                    "file_uri": file_uri,
                                }
                            },
                        ],
                    }
                ]

                response = self._model.generate_content(prompt)
                transcript = getattr(response, "text", None)
                if not transcript and getattr(response, "candidates", None):
                    for candidate in response.candidates:  # type: ignore[attr-defined]
                        content = getattr(candidate, "content", None)
                        if not content:
                            continue
                        parts = getattr(content, "parts", None)
                        if not parts:
                            continue
                        for part in parts:
                            if isinstance(part, str):
                                transcript = part
                                break
                            text_part = getattr(part, "text", None)
                            if text_part:
                                transcript = text_part
                                break
                        if transcript:
                            break
            finally:
                if tmp_path:
                    try:
                        os.unlink(tmp_path)
                    except FileNotFoundError:
                        pass
                    except Exception:  # pragma: no cover - defensive cleanup
                        self._logger.warning("Failed to remove temporary audio file %s", tmp_path)
                if uploaded is not None:
                    try:
                        name = getattr(uploaded, "name", None)
                        if name:
                            genai.delete_file(name)
                    except Exception:  # pragma: no cover - network cleanup
                        self._logger.warning(
                            "Failed to delete uploaded audio artifact %s",
                            getattr(uploaded, "name", filename),
                        )

            return transcript

        try:
            result = await asyncio.to_thread(_invoke)
        except Exception:  # pragma: no cover - network call
            self._logger.exception("Transcription failed for voice note %s", filename)
            return None

        if not result:
            return None
        stripped = result.strip()
        return stripped or None


__all__ = ["SpeechTranscriber"]
