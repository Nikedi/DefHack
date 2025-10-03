from __future__ import annotations

import base64
import warnings
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from ..settings import settings

try:  # pragma: no cover - optional heavy dependency
	from segment_anything import SamPredictor, sam_model_registry
except Exception:  # pragma: no cover - fallback when SAM is unavailable
	SamPredictor = None
	sam_model_registry = {}

SAM_MODEL_NAME = "vit_h"


def segment_soldiers(image: Any, detections: List[Dict[str, Any]], metadata: Optional[Dict[str, Any]] = None) -> List[str]:
    """Run the configured segmentation backend to produce masks for detections."""
    arr = _ensure_array(image, metadata)
    backend = getattr(settings, "segmentation_backend", "rectangle").lower()
    if backend == "fastseg":
        masks = _run_fastseg_backend(arr, detections)
        if masks is not None:
            return masks
        warnings.warn(
            "FastSeg backend unavailable or failed; falling back to rectangle masks.",
            RuntimeWarning,
        )
    elif backend == "sam":
        predictor = _load_sam_predictor(arr)
        if predictor is not None:
            try:
                return _run_sam_segmentation(predictor, arr, detections, metadata)
            except Exception as exc:  # pragma: no cover - guard against runtime issues
                warnings.warn(f"SAM segmentation failed ({exc}); using rectangle masks.", RuntimeWarning)
    return [_encode_mask(_rectangular_mask(arr.shape[:2], det["bounding_box"])) for det in detections]


def _run_fastseg_backend(image: np.ndarray, detections: List[Dict[str, Any]]) -> Optional[List[str]]:
    """Attempt to segment detections with FastSeg if the dependency is available."""
    model = _load_fastseg_model(settings.segmentation_model)
    if model is None:
        return None
    try:
        return _run_fastseg_segmentation(model, image, detections)
    except Exception:  # pragma: no cover - fall back silently and let caller warn
        return None


def _ensure_array(image: Any, metadata: Optional[Dict[str, Any]]) -> np.ndarray:
    if isinstance(image, np.ndarray):
        return image
    if metadata and "original_image" in metadata:
        return metadata["original_image"]
    raise TypeError("Segmentation expects an ndarray or preprocessing metadata with 'original_image'.")


def _load_fastseg_model(model_name: str | None):  # pragma: no cover - heavy optional dependency
    import importlib

    module_spec = importlib.util.find_spec("fastseg")
    if module_spec is None:
        return None
    fastseg_module = importlib.import_module("fastseg")
    constructor = getattr(fastseg_module, "MobileV3Large", None)
    alt_constructor = getattr(fastseg_module, "MobileV3Small", None)
    name = (model_name or "mobilev3large").lower()
    if "small" in name and alt_constructor is not None:
        constructor = alt_constructor
    if constructor is None or not hasattr(constructor, "from_pretrained"):
        return None
    try:
        model = constructor.from_pretrained().eval()
        return model
    except Exception:
        return None


def _run_fastseg_segmentation(model: Any, image: np.ndarray, detections: List[Dict[str, Any]]) -> List[str]:
    try:
        import torch
    except ImportError:  # pragma: no cover - torch missing
        return [_encode_mask(_rectangular_mask(image.shape[:2], det["bounding_box"])) for det in detections]

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    if hasattr(model, "to"):
        model = model.to(device)
    model.eval()
    input_tensor = torch.from_numpy(image.transpose(2, 0, 1)).float().unsqueeze(0) / 255.0
    input_tensor = input_tensor.to(device)

    with torch.no_grad():
        output = model(input_tensor)

    if isinstance(output, (list, tuple)):
        output = output[0]
    if hasattr(output, "detach"):
        output = output.detach()
    if output.dim() == 4:
        output = output.squeeze(0)

    # Derive a coarse binary foreground mask.
    if output.dim() == 3:
        prob_map = torch.softmax(output, dim=0).max(dim=0).values
    else:
        prob_map = torch.sigmoid(output).mean(dim=0)  # type: ignore[arg-type]
    mask_map = (prob_map > 0.5).cpu().numpy().astype(np.uint8)

    if mask_map.sum() == 0:
        return [_encode_mask(_rectangular_mask(image.shape[:2], det["bounding_box"])) for det in detections]

    encoded_masks: List[str] = []
    for det in detections:
        x1, y1, x2, y2 = det["bounding_box"]
        sub_mask = np.zeros_like(mask_map)
        sub_mask[y1:y2, x1:x2] = mask_map[y1:y2, x1:x2]
        if sub_mask[y1:y2, x1:x2].sum() == 0:
            sub_mask[y1:y2, x1:x2] = 1
        encoded_masks.append(_encode_mask(sub_mask))
    return encoded_masks


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
