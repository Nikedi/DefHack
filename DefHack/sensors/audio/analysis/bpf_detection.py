from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional

import numpy as np

from .signal_processing import amplitude_to_db, estimate_noise_floor


@dataclass(frozen=True)
class BPFDetection:
    fundamental_hz: Optional[float]
    harmonics: List[Dict[str, float]]
    peak_db: float
    noise_floor_db: float
    confidence: float
    description: str

    def as_dict(self) -> Dict[str, float | int | str | None]:
        return {
            "fundamental_hz": self.fundamental_hz,
            "harmonics": self.harmonics,
            "peak_db": self.peak_db,
            "noise_floor_db": self.noise_floor_db,
            "confidence": self.confidence,
            "description": self.description,
        }


def _find_peaks(values: np.ndarray) -> List[int]:
    if len(values) < 3:
        return []
    peaks = []
    for i in range(1, len(values) - 1):
        if values[i] > values[i - 1] and values[i] >= values[i + 1]:
            peaks.append(i)
    if not peaks:
        peaks.append(int(np.argmax(values)))
    return peaks


def detect_bpf(
    freq: np.ndarray,
    magnitude: np.ndarray,
    *,
    min_hz: float,
    max_hz: float,
    prominence_ratio: float,
    expected_harmonics: int,
) -> BPFDetection:
    mask = (freq >= min_hz) & (freq <= max_hz)
    if not np.any(mask):
        description = "Frequency window returned no candidates"
        return BPFDetection(None, [], -120.0, -120.0, 0.0, description)

    f_roi = freq[mask]
    mag_roi = magnitude[mask]
    db_roi = amplitude_to_db(mag_roi)
    noise_floor = estimate_noise_floor(db_roi)

    peak_indices = _find_peaks(db_roi)
    if not peak_indices:
        description = "No tonal components detected"
        return BPFDetection(None, [], noise_floor, noise_floor, 0.0, description)

    # Sort by amplitude descending
    peak_indices.sort(key=lambda idx: db_roi[idx], reverse=True)
    best_idx = peak_indices[0]
    fundamental = float(f_roi[best_idx])
    peak_db = float(db_roi[best_idx])
    snr = peak_db - noise_floor

    if snr < prominence_ratio:
        description = "No tonal peaks above noise floor"
        return BPFDetection(None, [], peak_db, noise_floor, 0.0, description)

    detection_window = max(fundamental * 0.03, 5.0)

    harmonics: List[Dict[str, float]] = []
    for order in range(1, expected_harmonics + 1):
        target = fundamental * order
        if target > f_roi[-1] + detection_window:
            break
        candidates = np.where(np.abs(f_roi - target) <= detection_window)[0]
        if len(candidates) == 0:
            continue
        best_candidate = max(candidates, key=lambda idx: db_roi[idx])
        candidate_db = float(db_roi[best_candidate])
        if candidate_db - noise_floor < prominence_ratio / 2.0:
            continue
        harmonics.append(
            {
                "order": float(order),
                "frequency_hz": float(f_roi[best_candidate]),
                "amplitude_db": candidate_db,
            }
        )

    harmonic_ratio = len(harmonics) / max(1, expected_harmonics)
    confidence = max(0.0, min(1.0, (snr / (prominence_ratio * 3.0)) + 0.35 * harmonic_ratio))

    if len(harmonics) == 0 or confidence < 0.2:
        description = "No convincing rotor signature detected"
        fundamental = None
        confidence = 0.0
        harmonics = []
    else:
        description = f"Dominant rotor tone at {fundamental:.1f} Hz with {len(harmonics)} harmonics"

    return BPFDetection(fundamental, harmonics, peak_db, noise_floor, confidence, description)
