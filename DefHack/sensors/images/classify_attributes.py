from __future__ import annotations

import base64
from typing import Any, Dict, List, Optional

import numpy as np


def classify_attributes(
    image: Any,
    detections: List[Dict[str, Any]],
    masks: List[str],
    metadata: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    """Classify uniform type, equipment, pose, etc. for each detection.

    A lightweight heuristic classifier is provided as a default implementation.
    """
    arr = _ensure_array(image, metadata)
    results: List[Dict[str, Any]] = []
    for det, mask_str in zip(detections, masks):
        mask = _decode_mask(mask_str, arr.shape[:2])
        if mask.sum() == 0:
            results.append(_default_classification())
            continue
        region_pixels = arr[mask.astype(bool)]
        mean_color = region_pixels.mean(axis=0)
        uniform_type = _infer_uniform_type(mean_color)
        equipment = _infer_equipment(mask)
        pose = _infer_pose(det["bounding_box"])
        results.append(
            {
                "uniform_type": uniform_type,
                "equipment": equipment,
                "pose": pose,
            }
        )
    return results


def _ensure_array(image: Any, metadata: Optional[Dict[str, Any]]) -> np.ndarray:
    if isinstance(image, np.ndarray):
        return image
    if metadata and "original_image" in metadata:
        return metadata["original_image"]
    raise TypeError("Classification expects an ndarray image or preprocessing metadata.")


def _decode_mask(mask_str: str, expected_shape) -> np.ndarray:
    header, data = mask_str.split(":", 1)
    h, w = map(int, header.split("x"))
    decoded = np.frombuffer(base64.b64decode(data), dtype=np.uint8)
    mask = np.unpackbits(decoded)[: h * w].reshape((h, w))
    if (h, w) != expected_shape:
        scaled_mask = np.zeros(expected_shape, dtype=np.uint8)
        min_h = min(expected_shape[0], h)
        min_w = min(expected_shape[1], w)
        scaled_mask[:min_h, :min_w] = mask[:min_h, :min_w]
        return scaled_mask
    return mask.astype(np.uint8)


def _infer_uniform_type(mean_color: np.ndarray) -> str:
    red, green, blue = mean_color.tolist()
    if green > red and green > blue:
        return "woodland_camouflage"
    if red > green and red > blue:
        return "desert_camouflage"
    return "urban_camouflage"


def _infer_equipment(mask: np.ndarray) -> List[str]:
    area_ratio = mask.mean()
    equipment = ["helmet"]
    if area_ratio > 0.05:
        equipment.append("rifle")
    if area_ratio > 0.12:
        equipment.append("backpack")
    return equipment


def _infer_pose(bbox) -> str:
    x1, y1, x2, y2 = bbox
    height = max(y2 - y1, 1)
    width = max(x2 - x1, 1)
    aspect_ratio = height / width
    if aspect_ratio > 1.3:
        return "standing"
    if aspect_ratio > 0.8:
        return "crouching"
    return "prone"


def _default_classification() -> Dict[str, Any]:
    return {
        "uniform_type": "unknown",
        "equipment": [],
        "pose": "unknown",
    }
