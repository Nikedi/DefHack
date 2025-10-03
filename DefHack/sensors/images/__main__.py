"""images class of sensors

This module implements the soldier recognition pipeline as described in documents/feature_implementation_plan.
"""

from statistics import mean
from typing import Any, Dict, List

from .prosses_image import preprocess_image
from .detect_soldiers import detect_soldiers
from .segment_soldiers import segment_soldiers
from .classify_attributes import classify_attributes
from .models import ImageIntelSchema


def soldier_recognition_pipeline(image: Any, **kwargs) -> ImageIntelSchema:
	"""Main pipeline: preprocess, detect, segment, classify, and construct intel schema."""
	preprocessed = preprocess_image(image)
	processed_image = preprocessed["image"]
	detections_raw = detect_soldiers(processed_image, preprocessed)
	masks = segment_soldiers(preprocessed["original_image"], detections_raw, preprocessed)
	classifications = classify_attributes(preprocessed["original_image"], detections_raw, masks, preprocessed)

	detections: List[Dict[str, Any]] = []
	for idx, det in enumerate(detections_raw):
		detection_entry = {
			"bounding_box": det.get("bounding_box", [0, 0, 0, 0]),
			"confidence": float(det.get("confidence", 0.0)),
			"mask": masks[idx] if idx < len(masks) else "",
			"classification": classifications[idx] if idx < len(classifications) else {},
		}
		detections.append(detection_entry)

	Timestamp = kwargs.get("Timestamp", "2025-10-03T00:00:00Z")
	Place = kwargs.get("Place", "Unknown")
	Count = kwargs.get("Count", len(detections))
	Type = kwargs.get("Type", "soldier")
	if "Confidence" in kwargs:
		Confidence = float(kwargs["Confidence"])
	else:
		confidences = [det["confidence"] for det in detections]
		Confidence = float(mean(confidences)) if confidences else 0.0
	Produced_by = kwargs.get("Produced_by", "pipeline_v1")

	base_meta = {
		"original_shape": preprocessed["original_shape"],
		"scale": preprocessed["scale"],
		"pad": preprocessed["pad"],
		"target_size": preprocessed["target_size"],
	}
	image_meta = {**base_meta, **kwargs.get("image_meta", {})}

	return ImageIntelSchema(Timestamp, Place, Count, Type, Confidence, Produced_by, detections, image_meta)


ImageIntelSchema.register_algorithm("default", soldier_recognition_pipeline)