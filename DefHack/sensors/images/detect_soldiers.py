from __future__ import annotations

import warnings
from functools import lru_cache
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from ..settings import settings

try:  # pragma: no cover - heavy dependency, optional at runtime
    from yolov5 import YOLO
except Exception:  # pragma: no cover - fallback when yolov5 not available
    YOLO = None


def detect_soldiers(image: Any, metadata: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """Run the configured detection backend to identify soldier candidates."""
    arr = _ensure_array(image)
    backend = getattr(settings, "detection_backend", "heuristic").lower()
    if backend == "tinyyolo":
        model = _load_tinyyolo_model(settings.detection_model)
        if model is not None:
            try:
                return _run_yolo_detection(model, arr, metadata)
            except Exception as exc:  # pragma: no cover - runtime safeguard
                warnings.warn(
                    f"TinyYOLO detection failed ({exc}); falling back to heuristic backend.",
                    RuntimeWarning,
                )
    return _heuristic_detection(arr, metadata)


def _ensure_array(image: Any) -> np.ndarray:
    if isinstance(image, np.ndarray):
        return image
    raise TypeError("Detection expects a numpy.ndarray image.")


@lru_cache(maxsize=1)
def _load_tinyyolo_model(model_name: str | None = None):  # pragma: no cover - heavy dependency
    if YOLO is None:
        return None
    name = (model_name or "yolov5n").strip() or "yolov5n"
    try:
        return YOLO(model=name)
    except Exception:
        return None


def _run_yolo_detection(model: Any, image: np.ndarray, metadata: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
    results = model.predict(image, imgsz=image.shape[0], verbose=False)
    detections: List[Dict[str, Any]] = []
    for result in results:
        for box in getattr(result, "boxes", []):
            x1, y1, x2, y2 = box.xyxy[0].tolist()
            score = float(box.conf[0])
            mapped_box = _map_box((x1, y1, x2, y2), metadata, image.shape)
            detections.append({"bounding_box": mapped_box, "confidence": score})
    return detections


def _heuristic_detection(image: np.ndarray, metadata: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
    gray = image.mean(axis=2)
    threshold = gray.mean() + 0.5 * gray.std()
    binary = gray > threshold
    components = _extract_components(binary)
    detections: List[Dict[str, Any]] = []
    for comp in components:
        if comp["area"] < 150:  # skip tiny regions
            continue
        x1, y1, x2, y2 = comp["bbox"]
        mapped_box = _map_box((x1, y1, x2, y2), metadata, image.shape)
        region = gray[y1:y2, x1:x2]
        confidence = float(np.clip(region.mean(), 0.0, 1.0))
        detections.append({"bounding_box": mapped_box, "confidence": confidence})
    return detections


def _map_box(box: Tuple[float, float, float, float], metadata: Optional[Dict[str, Any]], processed_shape: Tuple[int, int, int]) -> List[int]:
    if metadata is None:
        h, w = processed_shape[:2]
        x1, y1, x2, y2 = box
        x1 = int(np.clip(x1, 0, w - 1))
        y1 = int(np.clip(y1, 0, h - 1))
        x2 = int(np.clip(x2, x1 + 1, w))
        y2 = int(np.clip(y2, y1 + 1, h))
        return [x1, y1, x2, y2]

    pad_top, pad_left = metadata.get("pad", (0, 0))
    scale = metadata.get("scale", 1.0)
    original_h, original_w = metadata.get("original_shape", processed_shape[:2])
    x1, y1, x2, y2 = box
    x1 = max(int(round((x1 - pad_left) / scale)), 0)
    y1 = max(int(round((y1 - pad_top) / scale)), 0)
    x2 = min(int(round((x2 - pad_left) / scale)), original_w)
    y2 = min(int(round((y2 - pad_top) / scale)), original_h)
    x2 = max(x2, x1 + 1)
    y2 = max(y2, y1 + 1)
    return [x1, y1, x2, y2]


def _extract_components(binary: np.ndarray) -> List[Dict[str, Any]]:
    visited = np.zeros_like(binary, dtype=bool)
    components: List[Dict[str, Any]] = []
    h, w = binary.shape
    for y in range(h):
        for x in range(w):
            if not binary[y, x] or visited[y, x]:
                continue
            stack = [(y, x)]
            visited[y, x] = True
            y_min, x_min = y, x
            y_max, x_max = y, x
            count = 0
            while stack:
                sy, sx = stack.pop()
                count += 1
                y_min = min(y_min, sy)
                y_max = max(y_max, sy)
                x_min = min(x_min, sx)
                x_max = max(x_max, sx)
                for ny in range(max(0, sy - 1), min(h, sy + 2)):
                    for nx in range(max(0, sx - 1), min(w, sx + 2)):
                        if not binary[ny, nx] or visited[ny, nx]:
                            continue
                        visited[ny, nx] = True
                        stack.append((ny, nx))
            components.append(
                {
                    "area": count,
                    "bbox": (x_min, y_min, x_max + 1, y_max + 1),
                }
            )
    return components
