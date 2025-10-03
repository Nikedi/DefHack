from .. import SensorSchema
from typing import List, Dict, Any

class ImageIntelSchema(SensorSchema):
	"""
	Schema for intel extracted from forest images.
	Requires: Timestamp, Place, Count, Type, Confidence, Produced_by
	"""
	def __init__(self, Timestamp: str, Place: str, Count: int, Type: str, Confidence: float, Produced_by: str, detections: List[Dict[str, Any]], image_meta: Dict[str, Any] = None):
		super().__init__(Timestamp, Place, Count, Type, Confidence, Produced_by)
		self.detections = detections
		self.image_meta = image_meta or {}

	def to_dict(self) -> dict:
		return {
			"Timestamp": self.Timestamp,
			"Place": self.Place,
			"Count": self.Count,
			"Type": self.Type,
			"Confidence": self.Confidence,
			"Produced_by": self.Produced_by,
			"detections": self.detections,
			"image_meta": self.image_meta,
		}