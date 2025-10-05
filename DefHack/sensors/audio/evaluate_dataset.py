from __future__ import annotations

import argparse
import csv
import json
import re
import random
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

try:
    from tqdm import tqdm
except ImportError:  # pragma: no cover - tqdm is optional at runtime
    tqdm = None

from .config import load_config
from .pipeline import analyze_audio


@dataclass(frozen=True)
class FileMetadata:
    label: str
    configuration: Optional[str]
    mission: Optional[str]
    extras: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class EvaluationRecord:
    relative_path: str
    label: str
    configuration: Optional[str]
    mission: Optional[str]
    model: Optional[str]
    bearing_deg: Optional[float]
    range_m: Optional[float]
    altitude_m: Optional[float]
    temperature_k: Optional[float]
    sample_type: Optional[str]
    timestamp: Optional[str]
    flight_session_id: Optional[str]
    recording_session_id: Optional[str]
    sequence_id: Optional[str]
    detected: bool
    fundamental_hz: Optional[float]
    harmonics: int
    confidence_pct: int
    snr_db: Optional[float]
    peak_db: Optional[float]
    noise_floor_db: Optional[float]
    description: str


def _infer_metadata(root: Path, file_path: Path) -> FileMetadata:
    ddl_metadata = _parse_ddl_filename(file_path.name)
    if ddl_metadata:
        model = ddl_metadata["model"]
        label = model
        if label == "XXXX":
            label = "no_drone"
        extras = dict(ddl_metadata)
        extras["model"] = model
        return FileMetadata(
            label=label,
            configuration=None,
            mission=None,
            extras=extras,
        )

    try:
        relative = file_path.relative_to(root)
    except ValueError:
        relative = file_path
    parts = list(relative.parts)
    label: Optional[str] = None
    configuration: Optional[str] = None
    mission: Optional[str] = None

    if len(parts) >= 4 and parts[0].lower() == "dataset":
        # Dataset/<CLASS>/<CONFIG>/<MISSION>/<RUN>/<FILE>
        label = parts[1]
        configuration = parts[2]
        mission = parts[3]
    elif len(parts) >= 3:
        label = parts[0]
        configuration = parts[1]
        mission = parts[2]
    elif len(parts) >= 1:
        label = parts[0]

    if label is None:
        label = "UNKNOWN"
    return FileMetadata(label=label, configuration=configuration, mission=mission, extras={})
DDL_REGEX = re.compile(
    r"^(?P<timestamp>\d{14})(?P<model>[A-Z0-9]{4})(?P<bearing>\d{3})(?P<range>\d{3})(?P<altitude>[\d-]{3})(?P<temperature>\d{4})(?P<sample_type>[RS])(?P<flight_session>\d{6})-(?P<recording_session>[^-]+)-(\d+)$"
)


def _parse_ddl_filename(name: str) -> Optional[Dict[str, Any]]:
    stem = Path(name).stem
    match = DDL_REGEX.match(stem)
    if not match:
        return None

    groups = match.groupdict()
    try:
        bearing = float(groups["bearing"])
        range_m = float(groups["range"])
        altitude_token = groups["altitude"]
        altitude_str = altitude_token.replace("-", "") if altitude_token else ""
        altitude = float(altitude_str) if altitude_str else 0.0
        temperature = float(groups["temperature"]) / 10.0
    except ValueError:
        return None

    return {
        "timestamp": groups["timestamp"],
        "model": groups["model"],
        "bearing_deg": bearing,
        "range_m": range_m,
        "altitude_m": altitude,
        "temperature_k": temperature,
        "sample_type": "real" if groups["sample_type"] == "R" else "synthetic",
        "flight_session_id": groups["flight_session"],
        "recording_session_id": groups["recording_session"],
        "sequence_id": stem.split("-")[-1],
    }


def _iter_wav_files(root: Path) -> Iterable[Path]:
    for path in sorted(root.rglob("*.wav")):
        if path.is_file():
            yield path


def _balanced_shuffle(
    entries: Sequence[Tuple[Path, FileMetadata]],
    *,
    seed: Optional[int] = None,
) -> List[Tuple[Path, FileMetadata]]:
    if not entries:
        return []

    rng = random.Random(seed)
    buckets: Dict[str, List[Tuple[Path, FileMetadata]]] = defaultdict(list)
    for path, metadata in entries:
        buckets[metadata.label].append((path, metadata))

    labels = list(buckets.keys())
    rng.shuffle(labels)
    for label in labels:
        rng.shuffle(buckets[label])

    ordered: List[Tuple[Path, FileMetadata]] = []
    active = [label for label in labels if buckets[label]]

    while active:
        next_active: List[str] = []
        for label in active:
            bucket = buckets[label]
            if not bucket:
                continue
            ordered.append(bucket.pop())
            if bucket:
                next_active.append(label)
        active = next_active

    return ordered


def evaluate_dataset(
    root: Path,
    *,
    max_files: Optional[int] = None,
    overrides: Optional[Dict[str, Any]] = None,
    save_reports: bool = False,
    show_progress: bool = True,
    shuffle_seed: Optional[int] = None,
) -> List[EvaluationRecord]:
    root = root.expanduser().resolve()
    if not root.exists():
        raise FileNotFoundError(f"Dataset root '{root}' does not exist")

    config_overrides = overrides or {}
    results: List[EvaluationRecord] = []

    entries: List[Tuple[Path, FileMetadata]] = [
        (wav_path, _infer_metadata(root, wav_path)) for wav_path in _iter_wav_files(root)
    ]
    entries = _balanced_shuffle(entries, seed=shuffle_seed)

    if max_files is not None:
        entries = entries[:max_files]

    iterator: Iterable[Tuple[Path, FileMetadata]] = entries
    if tqdm is not None and show_progress:
        iterator = tqdm(
            entries,
            desc="Evaluating dataset",
            unit="file",
            total=len(entries),
            leave=False,
        )

    for wav_path, metadata in iterator:
        schema = analyze_audio(
            wav_path,
            overrides=config_overrides,
            place=f"{metadata.label}:{metadata.configuration}:{metadata.mission}",
            save_report=save_reports,
        )
        fundamental = schema.metadata.get("fundamental_hz")
        snr = schema.metadata.get("snr_db")
        extras = metadata.extras
        record = EvaluationRecord(
            relative_path=str(wav_path.relative_to(root)),
            label=metadata.label,
            configuration=metadata.configuration,
            mission=metadata.mission,
            model=extras.get("model"),
            bearing_deg=extras.get("bearing_deg"),
            range_m=extras.get("range_m"),
            altitude_m=extras.get("altitude_m"),
            temperature_k=extras.get("temperature_k"),
            sample_type=extras.get("sample_type"),
            timestamp=extras.get("timestamp"),
            flight_session_id=extras.get("flight_session_id"),
            recording_session_id=extras.get("recording_session_id"),
            sequence_id=extras.get("sequence_id"),
            detected=fundamental is not None,
            fundamental_hz=fundamental,
            harmonics=int(schema.metadata.get("harmonic_count", 0)),
            confidence_pct=int(schema.metadata.get("confidence_pct", 0)),
            snr_db=float(snr) if snr is not None else None,
            peak_db=schema.metadata.get("peak_db"),
            noise_floor_db=schema.metadata.get("noise_floor_db"),
            description=schema.summary,
        )
        results.append(record)

    return results


def _aggregate(results: Iterable[EvaluationRecord]) -> Dict[str, Any]:
    totals = defaultdict(
        lambda: {
            "count": 0,
            "detections": 0,
            "confidences": [],
            "fundamentals": [],
        }
    )
    for record in results:
        entry = totals[record.label]
        entry["count"] += 1
        entry["detections"] += int(record.detected)
        entry["confidences"].append(record.confidence_pct)
        if record.detected and record.fundamental_hz is not None:
            entry["fundamentals"].append(record.fundamental_hz)

    summary = {}
    for label, value in totals.items():
        count = value["count"]
        detections = value["detections"]
        avg_conf = sum(value["confidences"]) / count if count else 0.0
        avg_fundamental = (
            sum(value["fundamentals"]) / len(value["fundamentals"])
            if value["fundamentals"]
            else 0.0
        )
        summary[label] = {
            "count": count,
            "detections": detections,
            "detection_rate": detections / count if count else 0.0,
            "avg_confidence": avg_conf,
            "avg_fundamental_hz": avg_fundamental,
        }

    total_files = sum(value["count"] for value in summary.values())
    total_detections = sum(value["detections"] for value in summary.values())
    avg_conf = (
        sum(value["avg_confidence"] * value["count"] for value in summary.values()) / total_files
        if total_files
        else 0.0
    )

    return {
        "total_files": total_files,
        "total_detections": total_detections,
        "detection_rate": (total_detections / total_files) if total_files else 0.0,
        "avg_confidence": avg_conf,
        "per_label": summary,
    }


def _write_output(path: Path, records: List[EvaluationRecord], fmt: str = "csv") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fmt == "json":
        payload = [record.__dict__ for record in records]
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return

    fieldnames = [
        "relative_path",
        "label",
        "configuration",
        "mission",
        "model",
        "bearing_deg",
        "range_m",
        "altitude_m",
        "temperature_k",
        "sample_type",
        "timestamp",
        "flight_session_id",
        "recording_session_id",
        "sequence_id",
        "detected",
        "fundamental_hz",
        "harmonics",
        "confidence_pct",
        "snr_db",
        "peak_db",
        "noise_floor_db",
        "description",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for record in records:
            writer.writerow(record.__dict__)


def main(argv: Optional[List[str]] = None) -> None:
    parser = argparse.ArgumentParser(description="Evaluate acoustic detector on UAV propeller dataset")
    parser.add_argument("root", type=Path, help="Path to the UAV propeller dataset root directory")
    parser.add_argument("--max-files", type=int, default=None, help="Optional cap on number of files")
    parser.add_argument(
        "--override",
        action="append",
        default=[],
        metavar="KEY=VALUE",
        help="Override config values (e.g. min_bpf_hz=60)",
    )
    parser.add_argument("--output", type=Path, default=None, help="Optional path for CSV/JSON output")
    parser.add_argument(
        "--format",
        choices={"csv", "json"},
        default="csv",
        help="Output format when --output is provided",
    )
    parser.add_argument("--reports", action="store_true", help="Persist per-file text reports")
    parser.add_argument(
        "--no-progress",
        action="store_true",
        help="Disable the progress bar",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Shuffle seed for balanced sampling across labels",
    )
    args = parser.parse_args(argv)

    overrides: Dict[str, Any] = {}
    for override in args.override:
        key, sep, value = override.partition("=")
        if not sep:
            raise ValueError(f"Overrides must be KEY=VALUE, got '{override}'")
        overrides[key.strip()] = value.strip()

    # Validate overrides by instantiating configuration
    _ = load_config(overrides=overrides)

    records = evaluate_dataset(
        args.root,
        max_files=args.max_files,
        overrides=overrides,
        save_reports=args.reports,
        show_progress=not args.no_progress,
        shuffle_seed=args.seed,
    )
    summary = _aggregate(records)

    print("===== Acoustic Dataset Evaluation =====")
    print(f"Files processed: {summary['total_files']}")
    print(f"Detections: {summary['total_detections']} ({summary['detection_rate']*100:.1f}% )")
    print(f"Average confidence: {summary['avg_confidence']:.1f}%")
    for label, stats in summary["per_label"].items():
        rate = stats["detection_rate"] * 100.0
        avg_f = stats["avg_fundamental_hz"]
        print(
            f"  - {label}: {stats['detections']}/{stats['count']} detections ({rate:.1f}% ), "
            f"avg conf {stats['avg_confidence']:.1f}%, avg fundamental {avg_f:.1f} Hz"
        )

    if args.output:
        _write_output(args.output, records, fmt=args.format)
        print(f"Detailed results written to {args.output}")


if __name__ == "__main__":  # pragma: no cover
    main()
