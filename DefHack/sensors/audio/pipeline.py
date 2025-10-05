from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Tuple

import numpy as np

from .analysis import compute_fft, detect_bpf
from .config import AcousticConfig, load_config
from .models import RotorSpecification, simulate_rotor_noise
from .schemas import AcousticDroneSchema, build_no_detection_schema
from .utils import load_wav

_REPORT_DIR = Path(__file__).with_suffix("").parent / "data" / "processed"
_ALGORITHM_NAME = "acoustic_drone_bpf"


def _resolve_signal(
    sensor_input: Any,
    config: AcousticConfig,
    *,
    sample_rate: float | None,
    duration_s: float,
    rpm: float,
    blades: int,
    rotor_radius_m: float,
) -> Tuple[float, np.ndarray, Dict[str, Any]]:
    if sensor_input is None or (
        isinstance(sensor_input, str) and sensor_input.lower() == "simulate"
    ):
        spec = RotorSpecification(rpm=rpm, blades=blades, radius_m=rotor_radius_m)
        _, signal, sim_meta = simulate_rotor_noise(duration_s, config, spec=spec)
        sim_meta.update({"source": "simulation"})
        return config.sampling_rate, signal, sim_meta

    if isinstance(sensor_input, np.ndarray):
        sr = float(sample_rate or config.sampling_rate)
        return sr, sensor_input.astype(np.float32), {"source": "array"}

    if isinstance(sensor_input, (str, Path)):
        sr, signal = load_wav(sensor_input)
        return sr, signal.astype(np.float32), {"source": "file", "path": str(Path(sensor_input).resolve())}

    raise TypeError(
        "sensor_input must be None, a numpy array, or a path to a WAV file"
    )


def _write_report(report_path: Path, schema: AcousticDroneSchema) -> Path:
    report_path.parent.mkdir(parents=True, exist_ok=True)
    metadata = schema.metadata
    lines = [
        f"Timestamp: {schema.Timestamp}",
        f"Source: {metadata.get('source', 'unknown')}",
        f"Description: {schema.summary}",
        f"Confidence: {metadata.get('confidence_pct', 0)}%",
        f"Peak (dB): {metadata.get('peak_db', 'n/a')}",
        f"Noise floor (dB): {metadata.get('noise_floor_db', 'n/a')}",
    ]
    if metadata.get("harmonics"):
        lines.append("Harmonics:")
        for harmonic in metadata["harmonics"]:
            freq = harmonic["frequency_hz"]
            amplitude = harmonic["amplitude_db"]
            order = int(harmonic["order"])
            lines.append(f"  - Order {order}: {freq:.1f} Hz @ {amplitude:.1f} dB")
    if metadata.get("narrative"):
        lines.append("")
        lines.append(metadata["narrative"])
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return report_path


def analyze_audio(
    sensor_input: Any = None,
    *,
    config_path: str | Path | None = None,
    overrides: Dict[str, Any] | None = None,
    sample_rate: float | None = None,
    duration_s: float = 2.5,
    rpm: float | None = None,
    blades: int | None = None,
    rotor_radius_m: float = 0.165,
    place: str = "UNKNOWN",
    save_report: bool = False,
    report_path: str | Path | None = None,
) -> AcousticDroneSchema:
    config = load_config(config_path, overrides)
    rpm = rpm if rpm is not None else config.default_rpm
    blades = blades if blades is not None else config.default_blades

    sr, signal, signal_meta = _resolve_signal(
        sensor_input,
        config,
        sample_rate=sample_rate,
        duration_s=duration_s,
        rpm=rpm,
        blades=blades,
        rotor_radius_m=rotor_radius_m,
    )

    freq, magnitude = compute_fft(
        signal,
        sr,
        fft_size=config.fft_size,
        window=config.window,
    )

    detection = detect_bpf(
        freq,
        magnitude,
        min_hz=config.min_bpf_hz,
        max_hz=config.max_bpf_hz,
        prominence_ratio=config.prominence_ratio,
        expected_harmonics=config.num_harmonics,
    )

    now = datetime.now(tz=timezone.utc)
    noise_floor_db = detection.noise_floor_db
    peak_db = detection.peak_db
    snr = peak_db - noise_floor_db
    confidence_pct = int(round(detection.confidence * 100))
    confidence_pct = max(0, min(100, confidence_pct))
    metadata: Dict[str, Any] = {
        **signal_meta,
        "config": config.to_dict(),
        "confidence_pct": confidence_pct,
        "harmonics": detection.harmonics,
        "harmonic_count": len(detection.harmonics),
        "fundamental_hz": detection.fundamental_hz,
        "peak_db": peak_db,
        "noise_floor_db": noise_floor_db,
        "snr_db": snr,
        "description": detection.description,
    }

    if detection.fundamental_hz is None:
        schema = build_no_detection_schema(metadata.get("source", "unknown"))
        base_description = schema.summary
        base_narrative = schema.metadata.get("narrative")
        schema.metadata.update(metadata)
        schema.metadata["description"] = base_description
        if base_narrative:
            schema.metadata.setdefault("narrative", base_narrative)
    else:
        narrative = (
            f"Detected blade-pass frequency at {detection.fundamental_hz:.1f} Hz "
            f"with {len(detection.harmonics)} harmonics. Estimated SNR {snr:.1f} dB."
        )
        metadata["narrative"] = narrative
        schema = AcousticDroneSchema(
            timestamp=now,
            place=place,
            harmonic_count=len(detection.harmonics),
            detection_type="RotorAcousticDetection",
            confidence=confidence_pct,
            produced_by="AcousticBPF-1.0",
            metadata=metadata,
        )

    if save_report:
        destination = Path(report_path) if report_path else _REPORT_DIR / f"acoustic_report_{now:%Y%m%dT%H%M%SZ}.txt"
        written = _write_report(destination, schema)
        schema.metadata["report_path"] = str(written)

    return schema


def register_with_sensor_schema(sensor_schema_cls) -> None:
    sensor_schema_cls.register_algorithm(_ALGORITHM_NAME, lambda sensor_input, **kwargs: analyze_audio(sensor_input, **kwargs))
