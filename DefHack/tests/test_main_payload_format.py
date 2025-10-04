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



def test_deliver_readings_prints_payload_when_debug(monkeypatch, tmp_path, capsys):
	def fake_post(payload, **kwargs):
		return True

	monkeypatch.setattr("DefHack.__main__._post_payload", fake_post)
	backlog_file = tmp_path / "backlog.json"
	payload = {
		"time": "2025-10-04T16:30:00+00:00",
		"mgrs": "35VLG8472571866",
		"what": "TACTICAL:test",
		"confidence": 90,
		"sensor_id": "TEST",
		"observer_signature": "Bot",
	}
	_deliver_readings([payload], backlog_path=backlog_file, url="http://example", api_key=None, timeout=1.0, debug_payload=True)
	out = capsys.readouterr().out
	assert "Payload ready for POST" in out
	assert '"mgrs": "35VLG8472571866"' in out



def test_deliver_readings_silent_without_debug(monkeypatch, tmp_path, capsys):
	def fake_post(payload, **kwargs):
		return True

	monkeypatch.setattr("DefHack.__main__._post_payload", fake_post)
	backlog_file = tmp_path / "backlog.json"
	payload = {
		"time": "2025-10-04T16:30:00+00:00",
		"mgrs": "35VLG8472571866",
		"what": "TACTICAL:test",
		"confidence": 90,
		"sensor_id": "TEST",
		"observer_signature": "Bot",
	}
	_deliver_readings([payload], backlog_path=backlog_file, url="http://example", api_key=None, timeout=1.0, debug_payload=False)
	out = capsys.readouterr().out
	assert "Payload ready for POST" not in out
