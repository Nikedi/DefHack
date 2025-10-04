"""YOLOv8 detection pipeline producing :class:`SensorObservationIn` instances.

This module distills the standalone YOLOv8 + CLIP retrieval inference script into a
reusable pipeline that conforms to the :class:`SensorSchema` interface. Each
detected target (people or vehicles) generates a schema instance that can be
converted into canonical sensor readings for downstream consumers.
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Dict, List, Optional, Sequence, Tuple

import cv2
import torch
import torch.nn.functional as F
from PIL import Image
import open_clip
from ultralytics import YOLO

from ..SensorSchema import SensorObservationIn, SensorSchema

try:  # pragma: no cover - optional dependency during isolated tests
    from .. import settings as sensor_settings
except ImportError:  # pragma: no cover - fallback when settings module unavailable
    sensor_settings = None

# ---------------------------------------------------------------------------
# Model caches
# ---------------------------------------------------------------------------

_YOLO_MODELS: Dict[Tuple[str, str], YOLO] = {}
_CLIP_COMPONENTS: Dict[Tuple[str, str], Tuple[torch.nn.Module, Callable, Callable, torch.dtype]] = {}
_CORPUS_CACHE: Dict[Tuple[str, float, str, str], Tuple[List[str], Optional[torch.Tensor]]] = {}


TARGET_LABELS = {
"person", 
"car,"
"truck",
"bus,"
"train",
"airplane",
"boat",
"motorcycle",}


def _resolve_device(device: Optional[str] = None) -> str:
    if device is not None:
        return device
    return "cuda" if torch.cuda.is_available() else "cpu"


def _load_yolo_model(weights: str, device: str) -> YOLO:
    key = (weights, device)
    if key not in _YOLO_MODELS:
        model = YOLO(weights)
        _YOLO_MODELS[key] = model
    return _YOLO_MODELS[key]


def _normalise_clip_identifier(model_id: str) -> Tuple[str, Optional[str], str]:
    if "::" in model_id:
        base, pretrained = model_id.split("::", 1)
        resolved = f"{base.strip()}::{pretrained.strip()}"
        return base.strip(), pretrained.strip(), resolved
    return model_id, None, model_id


def _settings_overrides() -> Dict[str, str]:
    overrides: Dict[str, str] = {}
    if sensor_settings is None:
        return overrides

    config = getattr(sensor_settings, "settings", None)
    if config is None:
        return overrides

    weights_override = getattr(config, "yolov8_weights", None)
    if isinstance(weights_override, str) and weights_override.strip():
        overrides["weights"] = weights_override.strip()

    caption_model_override = getattr(config, "yolov8_caption_model", None)
    if isinstance(caption_model_override, str) and caption_model_override.strip():
        overrides["caption_model"] = caption_model_override.strip()

    preferred_device = getattr(config, "yolov8_device", None)
    if isinstance(preferred_device, str) and preferred_device.strip():
        overrides["device"] = preferred_device.strip().lower()

    extra = getattr(config, "extra", {}) or {}
    if not isinstance(extra, dict):  # pragma: no cover - guard against incorrect usage
        return overrides

    if "weights" not in overrides:
        weights = extra.get("yolov8_weights")
        if isinstance(weights, str) and weights.strip():
            overrides["weights"] = weights.strip()

    if "caption_model" not in overrides:
        caption_model = extra.get("yolov8_caption_model")
        if isinstance(caption_model, str) and caption_model.strip():
            overrides["caption_model"] = caption_model.strip()

    if "device" not in overrides:
        device_extra = extra.get("yolov8_device")
        if isinstance(device_extra, str) and device_extra.strip():
            overrides["device"] = device_extra.strip().lower()

    return overrides


def _get_clip_components(model_id: str, device: str) -> Tuple[torch.nn.Module, Callable, Callable, torch.dtype]:
    base_model, pretrained, resolved_id = _normalise_clip_identifier(model_id)
    key = (resolved_id, device)
    if key in _CLIP_COMPONENTS:
        return _CLIP_COMPONENTS[key]

    if pretrained:
        components = open_clip.create_model_from_pretrained(base_model, pretrained)
    else:
        components = open_clip.create_model_from_pretrained(base_model)

    if isinstance(components, tuple):
        if len(components) == 3:
            model, preprocess, tokenizer = components
        elif len(components) == 2:
            model, preprocess = components
            tokenizer = open_clip.get_tokenizer(base_model)
        else:  # pragma: no cover - defensive programming for future API changes
            raise RuntimeError(
                f"Unexpected number of components ({len(components)}) returned by open_clip.create_model_from_pretrained"
            )
    else:  # pragma: no cover - open_clip should always return a tuple
        raise RuntimeError("open_clip.create_model_from_pretrained returned an unexpected object")

    model = model.to(device)
    model.eval()
    dtype = next(model.parameters()).dtype

    _CLIP_COMPONENTS[key] = (model, preprocess, tokenizer, dtype)
    return _CLIP_COMPONENTS[key]


def _collect_target_detections(result, confidence_threshold: float) -> List[Tuple[List[float], float, str, int]]:
    boxes = getattr(result, "boxes", None)
    if boxes is None or len(boxes) == 0:
        return []

    names = result.names
    detections: List[Tuple[List[float], float, str, int]] = []

    for idx, (cls_val, conf_val) in enumerate(zip(boxes.cls.tolist(), boxes.conf.tolist())):
        cls_id = int(cls_val)
        label = None
        if isinstance(names, dict):
            label = names.get(cls_id)
        elif isinstance(names, list) and 0 <= cls_id < len(names):
            label = names[cls_id]
        if label not in TARGET_LABELS or conf_val < confidence_threshold:
            continue
        bbox = boxes.xyxy[idx].cpu().tolist()
        detections.append((bbox, float(conf_val), label, cls_id))

    return detections


def _filter_result_to_targets(result) -> None:
    boxes = getattr(result, "boxes", None)
    if boxes is None or len(boxes) == 0:
        return

    names = result.names
    keep_mask: List[bool] = []
    for cls_val in boxes.cls.tolist():
        cls_idx = int(cls_val)
        label = None
        if isinstance(names, dict):
            label = names.get(cls_idx)
        elif isinstance(names, list) and 0 <= cls_idx < len(names):
            label = names[cls_idx]
        if label in TARGET_LABELS:
            keep_mask.append(True)
        else:
            keep_mask.append(False)

    if not any(keep_mask):
        result.boxes = boxes[torch.zeros_like(boxes.cls, dtype=torch.bool)]
        return

    mask_tensor = torch.tensor(keep_mask, device=boxes.cls.device, dtype=torch.bool)
    result.boxes = boxes[mask_tensor]


def _extract_detection_crops(result, detections: Sequence[Tuple[List[float], float, str, int]]) -> List[Image.Image]:
    crops: List[Image.Image] = []
    if not detections:
        return crops

    orig_img = result.orig_img
    for bbox, _, _, _ in detections:
        x1, y1, x2, y2 = map(int, bbox)
        x1 = max(x1, 0)
        y1 = max(y1, 0)
        x2 = min(x2, orig_img.shape[1])
        y2 = min(y2, orig_img.shape[0])
        if x2 <= x1 or y2 <= y1:
            continue
        crop_bgr = orig_img[y1:y2, x1:x2]
        if crop_bgr.size == 0:
            continue
        crop_rgb = cv2.cvtColor(crop_bgr, cv2.COLOR_BGR2RGB)
        crops.append(Image.fromarray(crop_rgb))
    return crops


def _load_corpus(corpus_path: Optional[Path]) -> List[str]:
    if corpus_path is None:
        return []
    path = Path(corpus_path)
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as fp:
        return [line.strip() for line in fp if line.strip()]


def _get_corpus_embeddings(
    corpus_path: Optional[Path],
    *,
    model_id: str,
    device: str,
    tokenizer,
    model: torch.nn.Module,
) -> Tuple[List[str], Optional[torch.Tensor]]:
    if corpus_path is None:
        return [], None

    path = Path(corpus_path)
    if not path.exists():
        return [], None

    lines = _load_corpus(path)
    if not lines:
        return [], None

    stamp = path.stat().st_mtime
    cache_key = (str(path.resolve()), stamp, model_id, device)
    if cache_key in _CORPUS_CACHE:
        return _CORPUS_CACHE[cache_key]

    with torch.no_grad():
        text_tokens = tokenizer(lines)
        text_tokens = text_tokens.to(device)
        text_features = model.encode_text(text_tokens)
        text_features = text_features.float()
        text_features = F.normalize(text_features, dim=-1)

    _CORPUS_CACHE[cache_key] = (lines, text_features)
    return _CORPUS_CACHE[cache_key]


def _retrieve_captions(
    crops: Sequence[Image.Image],
    detections: Sequence[Tuple[List[float], float, str, int]],
    *,
    model_id: str,
    device: str,
    corpus_path: Optional[Path],
    top_k: int = 1,
) -> List[str]:
    if not crops:
        return []

    model, preprocess, tokenizer, model_dtype = _get_clip_components(model_id, device)
    corpus_lines, text_features = _get_corpus_embeddings(
        corpus_path,
        model_id=model_id,
        device=device,
        tokenizer=tokenizer,
        model=model,
    )

    # Prepare image batch
    images = []
    for crop in crops:
        tensor = preprocess(crop)
        if model_dtype.is_floating_point:
            tensor = tensor.to(dtype=model_dtype)
        images.append(tensor)

    image_batch = torch.stack(images).to(device)

    with torch.no_grad():
        image_features = model.encode_image(image_batch)
        image_features = image_features.float()
        image_features = F.normalize(image_features, dim=-1)

    captions: List[str] = []
    if text_features is None or not corpus_lines:
        for _, conf_score, label, _ in detections:
            captions.append(f"{label} detected (confidence {conf_score:.2f})")
        return captions

    similarities = image_features @ text_features.T
    k = max(1, min(top_k, similarities.shape[1]))
    top_scores, top_indices = similarities.topk(k, dim=-1)

    for idx in range(len(crops)):
        phrases = []
        for rank in range(k):
            text_idx = top_indices[idx, rank].item()
            score = top_scores[idx, rank].item()
            phrases.append(f"{corpus_lines[text_idx]} ({score:.2f})")
        captions.append("; ".join(phrases))

    return captions


@dataclass
class DetectionMetadata:
    bbox: Tuple[float, float, float, float]
    confidence: float
    label: str
    caption: Optional[str]


class Yolov8PersonCaptionSchema(SensorSchema):
    """Schema for a YOLOv8 target detection (person or car) augmented with CLIP retrieval."""

    DEFAULT_TYPE = "object"
    DEFAULT_UNIT = "count"
    DEFAULT_WEIGHTS = "yolov11n.pt"
    DEFAULT_CAPTION_MODEL = "MobileCLIP-S1::datacompdr"

    def __init__(
        self,
        *,
        timestamp: datetime,
        place: str,
        produced_by: str,
        detection_metadata: DetectionMetadata,
        image_path: Path,
        detection_index: int,
    ) -> None:
        super().__init__(
            Timestamp=timestamp,
            Place=place,
            Count=1,
            Type=detection_metadata.label or self.DEFAULT_TYPE,
            Confidence=max(0.0, min(detection_metadata.confidence * 100.0, 100.0)),
            Produced_by=produced_by,
        )
        self.detection_metadata = detection_metadata
        self.image_path = Path(image_path)
        self.detection_index = detection_index

    @property
    def caption(self) -> Optional[str]:
        return self.detection_metadata.caption

    @property
    def label(self) -> str:
        return self.detection_metadata.label

    @property
    def bbox(self) -> Tuple[float, float, float, float]:
        return self.detection_metadata.bbox

    @property
    def detection_confidence(self) -> float:
        return self.detection_metadata.confidence

    def to_sensor_reading(
        self,
        *,
        mgrs: str,
        sensor_id: Optional[str],
        observer_signature: str,
        what: Optional[str] = None,
        amount: Optional[float] = None,
        unit: Optional[str] = None,
        original_message: Optional[str] = None,
    ) -> SensorObservationIn:
        canonical_mgrs = mgrs.replace(" ", "").upper() or self.Place
        description = what or self.caption or self.Type
        return super().to_sensor_reading(
            mgrs=canonical_mgrs,
            what=description,
            sensor_id=sensor_id,
            observer_signature=observer_signature,
            amount=amount if amount is not None else 1.0,
            unit=unit or self.DEFAULT_UNIT,
            original_message=original_message,
        )

    # ------------------------------------------------------------------
    # Pipeline entry point
    # ------------------------------------------------------------------

    @classmethod
    def analyze_image(
        cls,
        image_path: Path,
        *,
        mgrs: str = "UNKNOWN",
        sensor_id: str = "YOLOv8-Pipeline",
        observer_signature: str = "YOLOv8 Inference",
        weights: str = DEFAULT_WEIGHTS,
        caption_model: str = DEFAULT_CAPTION_MODEL,
        confidence: float = 0.25,
        caption: bool = True,
        device: Optional[str] = None,
        caption_corpus: Optional[Path] = Path("src/bag_of_words.txt"),
        caption_top_k: int = 1,
    ) -> Tuple[List[SensorObservationIn], List["Yolov8PersonCaptionSchema"], Optional[object]]:
        """Run inference on an image and generate schema and sensor readings.

        Returns a tuple of ``(sensor_readings, schema_objects, raw_result)`` where
        ``raw_result`` is the Ultralytics result object that can be used for
        downstream visualisation (annotation, plotting, etc.).
        """

        overrides = _settings_overrides()
        if weights == cls.DEFAULT_WEIGHTS and "weights" in overrides:
            weights = overrides["weights"]
        if caption_model == cls.DEFAULT_CAPTION_MODEL and "caption_model" in overrides:
            caption_model = overrides["caption_model"]
        if device is None and "device" in overrides:
            device = overrides["device"]

        resolved_device = _resolve_device(device)
        model = _load_yolo_model(weights, resolved_device)

        results = model.predict(
            source=str(image_path),
            conf=confidence,
            verbose=False,
            save=False,
            device=resolved_device,
        )
        if not results:
            return [], [], None

        result = results[0]
        detections = _collect_target_detections(result, confidence_threshold=confidence)

        crops = _extract_detection_crops(result, detections) if caption else []
        captions: List[str] = []
        if caption and detections:
            try:
                captions = _retrieve_captions(
                    crops,
                    detections,
                    model_id=caption_model,
                    device=resolved_device,
                    corpus_path=caption_corpus,
                    top_k=caption_top_k,
                )
            except Exception as exc:  # pragma: no cover - safeguard runtime errors
                captions = [f"caption-error: {exc}"] * len(detections)

        timestamp = datetime.now(timezone.utc)
        place_value = mgrs.replace(" ", "").upper() if mgrs else "UNKNOWN"
        produced_by = f"YOLOv8({weights})"
        if caption:
            produced_by += f"+CLIP({caption_model})"

        schema_objects: List[Yolov8PersonCaptionSchema] = []
        detections_by_label: Dict[str, List[Yolov8PersonCaptionSchema]] = defaultdict(list)

        for idx, (bbox, conf_score, label, _cls_id) in enumerate(detections):
            caption_text = captions[idx] if idx < len(captions) else None
            metadata = DetectionMetadata(
                bbox=tuple(bbox),
                confidence=conf_score,
                label=label,
                caption=caption_text,
            )
            schema = cls(
                timestamp=timestamp,
                place=place_value,
                produced_by=produced_by,
                detection_metadata=metadata,
                image_path=image_path,
                detection_index=idx + 1,
            )
            schema_objects.append(schema)
            detections_by_label[schema.label].append(schema)

        sensor_readings: List[SensorObservationIn] = []
        for label, label_schemas in detections_by_label.items():
            count = len(label_schemas)
            if count == 0:
                continue
            avg_confidence = sum(s.detection_confidence for s in label_schemas) / count
            reading = SensorObservationIn(
                time=timestamp,
                mgrs=place_value,
                what=label,
                amount=float(count),
                confidence=int(round(max(0.0, min(avg_confidence * 100.0, 100.0)))),
                sensor_id=sensor_id,
                unit=cls.DEFAULT_UNIT,
                observer_signature=observer_signature,
                original_message=None,
            )
            sensor_readings.append(reading)

        _filter_result_to_targets(result)

        return sensor_readings, schema_objects, result


# Register the pipeline with the SensorSchema factory for optional discovery.
def _yolov8_person_caption_algorithm(sensor_input, **kwargs):
    _readings, schemas, _ = Yolov8PersonCaptionSchema.analyze_image(sensor_input, **kwargs)
    return schemas


SensorSchema.register_algorithm(
    "yolov8-person-caption",
    _yolov8_person_caption_algorithm,
)
