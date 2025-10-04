"""Image sensor pipeline package."""

__all__ = []

try:  # pragma: no cover - optional legacy pipeline components
    from .models import ImageIntelSchema  # type: ignore[attr-defined]
except ModuleNotFoundError:  # pragma: no cover - legacy pipeline not available
    ImageIntelSchema = None  # type: ignore[assignment]
else:  # pragma: no cover - executed when legacy pipeline present
    __all__.append("ImageIntelSchema")

try:  # pragma: no cover - optional legacy pipeline components
    from .__main__ import soldier_recognition_pipeline  # type: ignore[attr-defined]
except ModuleNotFoundError:  # pragma: no cover - legacy pipeline not available
    soldier_recognition_pipeline = None  # type: ignore[assignment]
else:  # pragma: no cover - executed when legacy pipeline present
    __all__.append("soldier_recognition_pipeline")
