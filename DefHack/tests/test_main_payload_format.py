from datetime import datetime, timezone

from DefHack.__main__ import _prepare_payloads
from DefHack.sensors.SensorSchema import SensorObservationIn


def _make_reading(**overrides):
	base = dict(
		time=datetime(2025, 10, 4, 12, 59, 37, 973725, tzinfo=timezone.utc),
		mgrs="unknown ",
		what="TACTICAL:soldier",
		amount=4,
		confidence=82,
		sensor_id="YOLOv8-Pipeline",
		unit="CamBot",
		observer_signature="YOLOv8 Inference",
		original_message=None,
	)
	base.update(overrides)
	return SensorObservationIn(**base)


def test_prepare_payload_matches_output_json_sample():
	reading = _make_reading()
	payloads = _prepare_payloads([reading], unit_override=None)

	assert len(payloads) == 1
	record = payloads[0]
	assert record["time"] == "2025-10-04T12:59:37+00:00"
	assert record["mgrs"] == "UNKNOWN"
	assert record["what"] == "soldier"
	assert record["confidence"] == 82
	assert record["sensor_id"] == "YOLOv8-Pipeline"
	assert record["observer_signature"] == "YOLOv8 Inference"
	assert record["amount"] == 4.0
	assert record["unit"] == "CamBot"
	assert "original_message" not in record


def test_prepare_payload_applies_unit_override():
	reading = _make_reading(unit="CamBot")
	payloads = _prepare_payloads([reading], unit_override="Recon Unit")
	assert payloads[0]["unit"] == "Recon Unit"


def test_prepare_payload_omits_optional_nulls():
	reading = _make_reading(amount=None, unit=None, original_message=None, sensor_id="EXT-SENSOR")
	record = _prepare_payloads([reading], unit_override=None)[0]
	assert "amount" not in record
	assert "unit" not in record
	assert "original_message" not in record
	assert record["sensor_id"] == "EXT-SENSOR"
