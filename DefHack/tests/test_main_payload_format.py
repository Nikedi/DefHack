from datetime import datetime, timezone

from DefHack.__main__ import _canonicalise_payload, _deliver_readings, _prepare_payloads
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


def test_canonicalise_payload_handles_backlog_dict_with_missing_fields():
	raw = {
		"time": "2025-10-04T16:30:00Z",
		"mgrs": None,
		"what": "TACTICAL:armored convoy",
		"confidence": "55",
		"amount": "3",
	}
	structured = _canonicalise_payload(raw, unit_override=None)
	assert structured["time"] == "2025-10-04T16:30:00+00:00"
	assert structured["mgrs"] == "UNKNOWN"
	assert structured["what"] == "armored convoy"
	assert structured["confidence"] == 55
	assert structured["sensor_id"] == "UNKNOWN"
	assert structured["observer_signature"] == "UNKNOWN"
	assert structured["amount"] == 3.0
	assert "unit" not in structured
	assert "original_message" not in structured


def test_canonicalise_payload_clamps_confidence_and_fills_unknowns():
	raw = {
		"time": "invalid",
		"mgrs": " 35vl g8472571866 ",
		"what": "",
		"confidence": 150,
		"sensor_id": None,
		"observer_signature": "",
	}
	structured = _canonicalise_payload(raw, unit_override="Alpha")
	assert structured["mgrs"] == "35VLG8472571866"
	assert structured["confidence"] == 100
	assert structured["what"] == "UNKNOWN"
	assert structured["sensor_id"] == "UNKNOWN"
	assert structured["observer_signature"] == "UNKNOWN"
	assert structured["unit"] == "Alpha"


def test_deliver_readings_debug_prints_payload(tmp_path, capsys):
	initial_payload = {
		"time": "2025-10-04T16:30:00Z",
		"mgrs": "35vl g8472571866",
		"what": "TACTICAL:infantry squad",
		"confidence": 70,
		"sensor_id": "SENSOR-1",
		"observer_signature": "Watcher",
		"amount": 2,
	}
	posted: list[dict[str, object]] = []

	def fake_poster(payload: dict[str, object], *, url: str, api_key: str | None, timeout: float) -> bool:
		posted.append(payload)
		return True

	backlog_path = tmp_path / "backlog.json"
	_deliver_readings(
		[initial_payload],
		backlog_path=backlog_path,
		url="http://example.test",
		api_key=None,
		timeout=1.0,
		debug_payloads=True,
		poster=fake_poster,
	)

	stdout = capsys.readouterr().out
	assert "DEBUG payload ->" in stdout
	assert '"sensor_id": "SENSOR-1"' in stdout
	assert posted == [_canonicalise_payload(initial_payload)]
