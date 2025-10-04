"""Sensor module configuration.

Edit :mod:`DefHack.sensors.settings` to choose which backends power the
object detection and segmentation stages. The defaults keep the fast
heuristics so the pipeline works out of the box, but you can switch to
stronger models (e.g. TinyYOLO or FastSeg) once the dependencies are
installed.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import ClassVar, Dict, List, Literal


DetectionBackend = Literal["heuristic", "tinyyolo"]
SegmentationBackend = Literal["rectangle", "fastseg", "sam"]
DetectionModelLiteral = Literal["yolo11n", "yolov8n", "yolov8n-finetune"]
CaptionModelLiteral = Literal["S0", "S1"]


@dataclass
class BackendSettings:
    """Settings that control which model backends are used."""

    detection_backend: DetectionBackend = "tinyyolo"
    detection_model: DetectionModelLiteral = "yolov8n-finetune"
    segmentation_backend: SegmentationBackend = "sam"
    segmentation_model: str = "mobilev3large"
    caption_model: CaptionModelLiteral = "S1"

    # YOLOv8 pipeline overrides / defaults
    yolov8_weights: str | None = None
    yolov8_caption_model: str | None = None
    yolov8_device: str | None = None

    # Derived convenience fields
    detection_weights: str | None = None
    labels: List[str] = field(default_factory=list)

    # Backwards-compatible extras bag
    extra: dict[str, str] = field(default_factory=dict)

    DETECTION_MODELS: ClassVar[Dict[str, Dict[str, object]]] = {
        "yolov8n-finetune": {
            "weights": "yolov8n-finetune.pt",
            "output_labels": [
                "camouflage_soldier",
                "weapon",
                "military_tank",
                "military_truck",
                "military_vehicle",
                "civilian",
                "soldier",
                "civilian_vehicle",
                "military_artillery",
                "trench",
                "military_aircraft",
                "military_warship",
            ],
        },
        "yolov8n": {
            "weights": "yolov8n.pt",
            "output_labels": [
                "person",
                "bicycle",
                "car",
                "motorcycle",
                "bus",
                "train",
                "truck",
                "boat",
                "airplane",
            ],
        },
        "yolo11n": {
            "weights": "yolo11n.pt",
            "output_labels": [
                "person",
                "bicycle",
                "car",
                "motorcycle",
                "bus",
                "train",
                "truck",
                "boat",
                "airplane",
            ],
        },
    }

    CAPTION_MODELS: ClassVar[Dict[str, str]] = {
        "S0": "MobileCLIP-S0::datacompa",
        "S1": "MobileCLIP-S1::datacompdr",
    }

    def __post_init__(self) -> None:
        # normalise backend identifiers
        self.detection_backend = self.detection_backend.lower()  # type: ignore[assignment]
        self.segmentation_backend = self.segmentation_backend.lower()  # type: ignore[assignment]

        # apply detection model defaults
        model_cfg = self.DETECTION_MODELS.get(self.detection_model)
        if model_cfg:
            weights = model_cfg.get("weights")
            labels = model_cfg.get("output_labels", [])
            if not self.yolov8_weights:
                self.yolov8_weights = weights if isinstance(weights, str) else None
            self.detection_weights = weights if isinstance(weights, str) else None
            self.labels = list(labels) if isinstance(labels, list) else []
        else:
            self.detection_weights = None
            self.labels = []

        # apply caption model defaults
        caption_spec = self.CAPTION_MODELS.get(self.caption_model)
        if caption_spec and not self.yolov8_caption_model:
            self.yolov8_caption_model = caption_spec

        if self.yolov8_device:
            self.yolov8_device = self.yolov8_device.lower()


settings = BackendSettings()


def configure(**kwargs) -> None:
    """Update the global backend settings."""

    for key, value in kwargs.items():
        if not hasattr(settings, key):  # pragma: no cover - guard for typos
            raise AttributeError(f"Unknown settings field '{key}'.")
        setattr(settings, key, value)
    settings.__post_init__()