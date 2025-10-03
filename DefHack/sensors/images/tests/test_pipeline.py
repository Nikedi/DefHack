import base64
from DefHack.conftests import dummy_image
from .. import ImageIntelSchema, soldier_recognition_pipeline

def test_pipeline_runs(dummy_image):
	result = soldier_recognition_pipeline(
		dummy_image,
		Timestamp="2025-10-03T12:00:00Z",
		Place="Test Forest",
		Produced_by="unit-test",
	)
	assert isinstance(result, ImageIntelSchema)
	data = result.to_dict()
	assert data["Timestamp"] == "2025-10-03T12:00:00Z"
	assert data["Place"] == "Test Forest"
	assert data["Produced_by"] == "unit-test"
	assert data["Count"] == len(data["detections"])
	assert "image_meta" in data
	assert "original_shape" in data["image_meta"]
	assert data["detections"]

	for detection in data["detections"]:
		assert len(detection["bounding_box"]) == 4
		assert "classification" in detection
		assert detection["classification"]["uniform_type"]
		assert detection["mask"]
		header, payload = detection["mask"].split(":", 1)
		assert "x" in header
		base64.b64decode(payload)