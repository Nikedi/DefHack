from typing import Any, Dict, Type

class SensorSchema:
	"""
	Superclass for schemas produced from arbitrary sensor input.
	Provides a factory for algorithms that convert sensor input into schema instances.
	Requires fields: Timestamp, Place, Count, Type, Confidence, Produced_by.
	"""
	# Registry for conversion algorithms: {algorithm_name: callable}
	_algorithm_factory: Dict[str, Any] = {}

	@classmethod
	def register_algorithm(cls, name: str, algorithm: Any):
		"""Register a conversion algorithm by name."""
		cls._algorithm_factory[name] = algorithm

	@classmethod
	def from_sensor(cls, sensor_input: Any, algorithm: str = None, **kwargs) -> 'SensorSchema':
		"""
		Convert sensor input to schema using the specified algorithm.
		If no algorithm is specified, use the default (first registered).
		"""
		if not cls._algorithm_factory:
			raise ValueError("No algorithms registered for schema conversion.")
		if algorithm is None:
			algorithm = next(iter(cls._algorithm_factory))
		if algorithm not in cls._algorithm_factory:
			raise ValueError(f"Algorithm '{algorithm}' not registered.")
		return cls._algorithm_factory[algorithm](sensor_input, **kwargs)

	def __init__(self, Timestamp: str, Place: str, Count: int, Type: str, Confidence: float, Produced_by: str):
		self.Timestamp = Timestamp
		self.Place = Place
		self.Count = Count
		self.Type = Type
		self.Confidence = Confidence
		self.Produced_by = Produced_by

	def to_dict(self) -> dict:
		"""Convert schema instance to dictionary."""
		return {
			"Timestamp": self.Timestamp,
			"Place": self.Place,
			"Count": self.Count,
			"Type": self.Type,
			"Confidence": self.Confidence,
			"Produced_by": self.Produced_by,
		}