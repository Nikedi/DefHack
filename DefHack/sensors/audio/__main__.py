from __future__ import annotations

import argparse
import json
from pathlib import Path

from ..images.ingest import (
    DEFAULT_API_KEY,
    DEFAULT_API_URL,
    DEFAULT_UNIT_LABEL,
    _deliver_readings,
    _prepare_payloads,
)

from . import analyze_audio


TACTICAL_PREFIX = "TACTICAL:"
DEFAULT_UNIT = DEFAULT_UNIT_LABEL
DEFAULT_BACKLOG_PATH = Path("DefHack/sensors/audio/backlog.json")


def _write_sensor_readings_json(destination: Path, readings) -> None:
    destination = destination.expanduser()
    destination.parent.mkdir(parents=True, exist_ok=True)
    payload = [reading.model_dump() for reading in readings]
    with destination.open("w", encoding="utf-8") as fp:
        json.dump(payload, fp, indent=2, default=str)
    print(f"Sensor readings written to {destination}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Acoustic drone detection via blade-pass analysis")
    parser.add_argument("input", nargs="?", help="Path to WAV file. If omitted, a synthetic signal is simulated.")
    parser.add_argument("--report", action="store_true", help="Persist a text report to the processed/ directory")
    parser.add_argument("--place", "--mgrs", dest="mgrs", default="UNKNOWN", help="Optional MGRS or textual location tag")
    parser.add_argument("--rpm", type=float, default=None, help="Expected rotor RPM (for simulation mode)")
    parser.add_argument("--blades", type=int, default=None, help="Rotor blade count (for simulation mode)")
    parser.add_argument("--duration", type=float, default=2.5, help="Duration in seconds for simulated captures")
    parser.add_argument("--config", type=Path, default=None, help="Optional path to override config.yaml")
    parser.add_argument("--sensor-id", default="AcousticBPF-Pipeline", help="Sensor identifier embedded in SensorObservationIn output")
    parser.add_argument("--observer", default="SENSOR:AcousticBPF", help="Observer signature for SensorObservationIn output")
    parser.add_argument(
        "--readings-json",
        type=Path,
        default=Path("DefHack/sensors/audio/predictions.json"),
        help="Optional path to write SensorObservationIn payload as JSON",
    )
    parser.add_argument("--api-url", default=DEFAULT_API_URL, help="Target ingestion endpoint URL")
    parser.add_argument("--api-key", default=DEFAULT_API_KEY, help="API key for the ingestion endpoint")
    parser.add_argument(
        "--backlog-file",
        type=Path,
        default=DEFAULT_BACKLOG_PATH,
        help="Path to persist undelivered sensor readings",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=5.0,
        help="Seconds before HTTP POST attempts time out",
    )
    parser.add_argument("--debug-payloads", action="store_true", help="Print payload JSON before posting to the API")
    parser.add_argument("--no-send", dest="send_payloads", action="store_false", help="Skip posting observations to the ingestion endpoint")
    parser.add_argument("--send", dest="send_payloads", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--no-summary", dest="summary", action="store_false", help="Suppress console summary output")
    parser.add_argument("--summary", dest="summary", action="store_true", help=argparse.SUPPRESS)
    parser.set_defaults(summary=True, send_payloads=True)
    args = parser.parse_args()

    args.backlog_file = args.backlog_file.expanduser().resolve()
    if args.readings_json:
        args.readings_json = args.readings_json.expanduser()

    schema = analyze_audio(
        args.input,
        config_path=args.config,
        duration_s=args.duration,
        rpm=args.rpm,
        blades=args.blades,
        place=args.mgrs,
        save_report=args.report,
    )

    summary_text = schema.summary or ""
    confidence_pct = int(schema.metadata.get("confidence_pct", 0))
    detected = schema.metadata.get("fundamental_hz") is not None
    status = "FPV DETECTED" if detected else "NO FPV DETECTED"

    base_message = summary_text.strip()
    if base_message:
        enriched_message = f"{status} (confidence {confidence_pct-3.2}%) - {base_message}"
    else:
        enriched_message = f"{status} (confidence {confidence_pct}%)"

    normalized = enriched_message.lstrip()
    if not normalized.upper().startswith(TACTICAL_PREFIX):
        description = f"{TACTICAL_PREFIX} {enriched_message}".strip()
    else:
        description = enriched_message

    observation = schema.to_sensor_message(
        mgrs=args.mgrs,
        sensor_id=args.sensor_id,
        observer_signature=args.observer,
        unit=DEFAULT_UNIT,
        what=description,
    )
    readings = [observation]

    if args.summary:
        print("=== Acoustic Drone Detection ===")
        print(schema.summary)
        print(f"Confidence: {schema.metadata.get('confidence_pct', 0)}%")
        if schema.metadata.get("fundamental_hz"):
            print(f"Fundamental Frequency: {schema.metadata['fundamental_hz']:.1f} Hz")
            print(f"Harmonics Detected: {schema.metadata.get('harmonic_count', 0)}")
        if "report_path" in schema.metadata:
            print(f"Report saved to: {schema.metadata['report_path']}")
        print("\nSensor Observation Payload:")
        print(observation.model_dump_json(indent=2))

    if args.send_payloads and readings:
        args.backlog_file.parent.mkdir(parents=True, exist_ok=True)
        payloads = _prepare_payloads(readings, unit_override=DEFAULT_UNIT)
        _deliver_readings(
            payloads,
            backlog_path=args.backlog_file,
            url=args.api_url,
            api_key=args.api_key or None,
            timeout=max(0.5, float(args.timeout)),
            debug_payloads=args.debug_payloads,
        )

    if args.readings_json and readings:
        _write_sensor_readings_json(args.readings_json, readings)


if __name__ == "__main__":
    main()
