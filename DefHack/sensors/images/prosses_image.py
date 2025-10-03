from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Tuple

import numpy as np

try:  # Optional dependency – used if available for loading from disk
    from PIL import Image
except ImportError:  # pragma: no cover - pillow is optional
    Image = None

TARGET_SIZE: Tuple[int, int] = (640, 640)


def preprocess_image(image: Any, target_size: Tuple[int, int] = TARGET_SIZE) -> Dict[str, Any]:
    """Normalize, resize, and augment image as needed.

    The function returns a dictionary with the preprocessed image alongside
    metadata required by later stages of the pipeline.
    """
    array = _load_image(image)
    original_shape = array.shape[:2]
    normalized = _normalize(array)
    processed, scale, pad = _resize_with_padding(normalized, target_size)

    meta: Dict[str, Any] = {
        "image": processed,
        "original_image": normalized,
        "original_shape": original_shape,
        "scale": scale,
        "pad": pad,
        "target_size": target_size,
    }
    return meta


def _load_image(image: Any) -> np.ndarray:
    if isinstance(image, np.ndarray):
        arr = image
    elif Image is not None and isinstance(image, Image.Image):  # pragma: no cover - depends on pillow
        arr = np.asarray(image)
    elif isinstance(image, (str, Path)):
        if Image is None:
            raise ValueError("Pillow is required to load images from disk.")
        with Image.open(image) as img:  # pragma: no cover - depends on pillow
            arr = np.asarray(img.convert("RGB"))
    else:
        raise TypeError("Unsupported image type for preprocessing.")

    if arr.ndim == 2:  # grayscale -> RGB
        arr = np.stack([arr] * 3, axis=-1)
    if arr.shape[-1] != 3:
        raise ValueError("Expected an image with 3 channels (RGB).")
    return arr


def _normalize(array: np.ndarray) -> np.ndarray:
    arr = array.astype(np.float32)
    if arr.max() > 1.0:
        arr /= 255.0
    return np.clip(arr, 0.0, 1.0)


def _resize_with_padding(image: np.ndarray, target_size: Tuple[int, int]) -> Tuple[np.ndarray, float, Tuple[int, int]]:
    target_h, target_w = target_size
    h, w = image.shape[:2]
    if (h, w) == target_size:
        return image, 1.0, (0, 0)

    scale = min(target_h / h, target_w / w)
    new_h = max(1, int(round(h * scale)))
    new_w = max(1, int(round(w * scale)))
    resized = _resize_nearest(image, (new_h, new_w))
    pad_top = (target_h - new_h) // 2
    pad_left = (target_w - new_w) // 2
    pad_bottom = target_h - new_h - pad_top
    pad_right = target_w - new_w - pad_left
    padded = np.pad(
        resized,
        ((pad_top, pad_bottom), (pad_left, pad_right), (0, 0)),
        mode="constant",
        constant_values=0.0,
    )
    return padded, scale, (pad_top, pad_left)


def _resize_nearest(image: np.ndarray, size: Tuple[int, int]) -> np.ndarray:
    new_h, new_w = size
    h, w = image.shape[:2]
    y_indices = np.linspace(0, h - 1, new_h).astype(np.int32)
    x_indices = np.linspace(0, w - 1, new_w).astype(np.int32)
    return image[y_indices[:, None], x_indices[None, :], :]
