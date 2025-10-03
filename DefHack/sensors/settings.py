"""Sensor module configuration.

Edit :mod:`DefHack.sensors.settings` to choose which backends power the
object detection and segmentation stages.  The defaults keep the fast
heuristics so the pipeline works out-of-the-box, but you can switch to
stronger models (e.g. TinyYOLO or FastSeg) once the dependencies are
installed.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

DetectionBackend = Literal["heuristic", "tinyyolo"]
SegmentationBackend = Literal["rectangle", "fastseg", "sam"]


@dataclass
class BackendSettings:
    """Settings that control which model backends are used.

    Attributes
    ----------
    detection_backend:
        Backend used by :func:`detect_soldiers`.  ``"heuristic"`` is the
        default lightweight implementation, while ``"tinyyolo"`` enables a
        TinyYOLO (yolov5n) model when available.
    detection_model:
        Optional model identifier passed to the detection backend.  For
        TinyYOLO the default is ``"yolov5n"``.
    segmentation_backend:
        Backend used by :func:`segment_soldiers`.  ``"rectangle"`` keeps the
        fast rectangle-based masks, ``"fastseg"`` attempts to run a FastSeg
        semantic model when the dependency is installed, and ``"sam"`` is
        reserved for future use.
    segmentation_model:
        Optional model identifier passed to the segmentation backend.
    """

    detection_backend: DetectionBackend = "tinyyolo"
    detection_model: str = "yolov5n"
    segmentation_backend: SegmentationBackend = "sam"
    segmentation_model: str = "mobilev3large"
    extra: dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.detection_backend = self.detection_backend.lower()  # type: ignore[assignment]
        self.segmentation_backend = self.segmentation_backend.lower()  # type: ignore[assignment]


settings = BackendSettings()


def configure(**kwargs) -> None:
    """Update the global backend settings.

    Example
    -------
    >>> from DefHack.sensors import settings
    >>> settings.configure(detection_backend="tinyyolo", segmentation_backend="fastseg")
    """

    for key, value in kwargs.items():
        if not hasattr(settings, key):  # pragma: no cover - guard for typos
            raise AttributeError(f"Unknown settings field '{key}'.")
        setattr(settings, key, value)
    settings.__post_init__()
