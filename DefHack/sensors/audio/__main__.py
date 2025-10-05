from __future__ import annotations

import argparse
import json
from pathlib import Path

from . import analyze_audio


TACTICAL_PREFIX = "TACTICAL:"
DEFAULT_UNIT = "Alpha Company"


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
    parser.add_argument("--observer", default="AcousticBPF", help="Observer signature for SensorObservationIn output")
    parser.add_argument(
        "--readings-json",
        type=Path,
        default=Path("DefHack/sensors/audio/predictions.json"),
        help="Optional path to write SensorObservationIn payload as JSON",
    )
    parser.add_argument("--no-summary", dest="summary", action="store_false", help="Suppress console summary output")
    parser.add_argument("--summary", dest="summary", action="store_true", help=argparse.SUPPRESS)
    parser.set_defaults(summary=True)
    args = parser.parse_args()

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
    normalized = summary_text.lstrip()
    if not normalized.upper().startswith(TACTICAL_PREFIX):
        if normalized:
            description = f"{TACTICAL_PREFIX} {summary_text}".strip()
        else:
            description = TACTICAL_PREFIX
    else:
        description = summary_text

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

    if args.readings_json and readings:
        _write_sensor_readings_json(args.readings_json, readings)


if __name__ == "__main__":
    main()
