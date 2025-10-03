from __future__ import annotations

import base64
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

try:  # pragma: no cover - optional heavy dependency
    from segment_anything import SamPredictor, sam_model_registry
except Exception:  # pragma: no cover - fallback when SAM is unavailable
    SamPredictor = None
    sam_model_registry = {}

SAM_MODEL_NAME = "vit_h"


def segment_soldiers(image: Any, detections: List[Dict[str, Any]], metadata: Optional[Dict[str, Any]] = None) -> List[str]:
    """Run SAM or similar to get masks for each detection.

    When the official SAM model cannot be loaded, the function falls back to
    creating simple rectangular masks from the detected bounding boxes.
    """
    arr = _ensure_array(image, metadata)
    predictor = _load_sam_predictor(arr)
    if predictor is not None:
        try:
            return _run_sam_segmentation(predictor, arr, detections, metadata)
        except Exception:  # pragma: no cover - guard against runtime issues
            pass
    return [_encode_mask(_rectangular_mask(arr.shape[:2], det["bounding_box"])) for det in detections]


def _ensure_array(image: Any, metadata: Optional[Dict[str, Any]]) -> np.ndarray:
    if isinstance(image, np.ndarray):
        return image
    if metadata and "original_image" in metadata:
        return metadata["original_image"]
    raise TypeError("Segmentation expects an ndarray or preprocessing metadata with 'original_image'.")


def _load_sam_predictor(image: np.ndarray):  # pragma: no cover - requires SAM weights
    if SamPredictor is None:
        return None
    if not sam_model_registry:
        return None
    model_constructor = sam_model_registry.get(SAM_MODEL_NAME)
    if model_constructor is None:
        return None
    try:
        model = model_constructor(checkpoint=None)
    except Exception:
        return None
    predictor = SamPredictor(model)
    predictor.set_image((image * 255).astype(np.uint8))
    return predictor


def _run_sam_segmentation(predictor: Any, image: np.ndarray, detections: List[Dict[str, Any]], metadata: Optional[Dict[str, Any]]) -> List[str]:
    masks: List[str] = []
    for det in detections:
        x1, y1, x2, y2 = det["bounding_box"]
        box = np.array([[x1, y1], [x2, y2]], dtype=np.float32)
        mask, _, _ = predictor.predict(point_coords=None, point_labels=None, box=box[None, ...], multimask_output=False)
        binary_mask = mask[0].astype(np.uint8)
        masks.append(_encode_mask(binary_mask))
    return masks


def _rectangular_mask(shape: Tuple[int, int], bbox: List[int]) -> np.ndarray:
    mask = np.zeros(shape, dtype=np.uint8)
    x1, y1, x2, y2 = bbox
    mask[y1:y2, x1:x2] = 1
    return mask


def _encode_mask(mask: np.ndarray) -> str:
    flat = mask.astype(np.uint8).flatten()
    packed = np.packbits(flat)
    header = f"{mask.shape[0]}x{mask.shape[1]}:"
    return header + base64.b64encode(packed.tobytes()).decode("ascii")
