import base64
from pathlib import Path

import pytest
from PIL import Image

from .. import ImageIntelSchema, soldier_recognition_pipeline

pytestmark = pytest.mark.skipif(
	ImageIntelSchema is None or soldier_recognition_pipeline is None,
	reason="Legacy image pipeline not available in this build",
)

def test_pipeline_runs(dummy_image):
	result = soldier_recognition_pipeline(
		dummy_image,
		Timestamp="2025-10-03T12:00:00Z",
		Place="Test Forest",
		Produced_by="unit-test",
	)
	assert isinstance(result, ImageIntelSchema)
	reading = result.to_dict(
		mgrs="32VNM1234567890",
		what="soldier",
		sensor_id="sensor-001",
		observer_signature="Sensor 1, Team A",
	)
	assert reading.time.isoformat().startswith("2025-10-03T12:00:00")
	assert reading.mgrs == "32VNM1234567890"
	assert reading.what == "soldier"
	assert reading.amount == float(result.Count)
	assert reading.confidence == int(round(result.Confidence))
	assert reading.sensor_id == "sensor-001"
	assert reading.observer_signature == "Sensor 1, Team A"

	assert result.detections
	assert result.image_meta
	assert "original_shape" in result.image_meta
	assert result.image_meta["detection_backend"]
	assert result.image_meta["segmentation_backend"]

	for detection in result.detections:
		assert len(detection["bounding_box"]) == 4
		assert "classification" in detection
		assert detection["classification"]["uniform_type"]
		assert detection["mask"]
		header, payload = detection["mask"].split(":", 1)
		assert "x" in header
		base64.b64decode(payload)


@pytest.mark.integration
def test_pipeline_real_image(tmp_path):
	image_path = Path(__file__).with_name("test_img_1.jpg")
	assert image_path.exists(), "Expected test image not found"

	with Image.open(image_path) as img:
		width, height = img.size

	result = soldier_recognition_pipeline(
		str(image_path),
		Timestamp="2025-10-03T12:05:00Z",
		Place="Demo Forest",
		Produced_by="unit-test",
	)
	reading = result.to_dict(
		mgrs="32VNM1234567890",
		what="soldier",
		sensor_id="sensor-001",
		observer_signature="Sensor 1, Team A",
	)

	assert isinstance(result, ImageIntelSchema)
	assert reading.confidence >= 0
	assert reading.confidence <= 100
	assert reading.amount == float(result.Count)
	assert result.image_meta["original_shape"] == (height, width)
	assert result.image_meta["detection_backend"]
	assert result.image_meta["segmentation_backend"]

	for detection in result.detections:
		x1, y1, x2, y2 = detection["bounding_box"]
		assert 0 <= x1 < x2 <= width
		assert 0 <= y1 < y2 <= height
		assert detection["mask"]
		header, payload = detection["mask"].split(":", 1)
		assert "x" in header
		base64.b64decode(payload)