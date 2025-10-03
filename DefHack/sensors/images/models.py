from ..SensorSchema import SensorSchema, SensorReading
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

	def to_dict(self, **kwargs) -> SensorReading:
		"""
		Return a SensorReading instance representing this schema.
		Extra kwargs are passed to to_sensor_reading.
		"""
		# You must provide mgrs, what, sensor_id, observer_signature (and optionally amount, unit)
		return self.to_sensor_reading(**kwargs)