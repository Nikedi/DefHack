
import pytest
from .. import soldier_recognition_pipeline, ImageIntelSchema

def test_pipeline_runs(dummy_image):
	result = soldier_recognition_pipeline(dummy_image, image_id="test.jpg", timestamp="2025-10-03T12:00:00Z")
	assert isinstance(result, ImageIntelSchema)
	d = result.to_dict()
	assert "image_id" in d
	assert "timestamp" in d
	assert "detections" in d
	assert isinstance(d["detections"], list)