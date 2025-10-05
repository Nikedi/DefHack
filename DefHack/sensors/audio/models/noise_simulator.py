from __future__ import annotations

import math
from typing import Dict, Tuple

import numpy as np

from .acoustic_model import RotorSpecification


def simulate_rotor_noise(
    duration_s: float,
    config,
    *,
    spec: RotorSpecification,
    harmonics: int | None = None,
    noise_level: float | None = None,
) -> Tuple[np.ndarray, np.ndarray, Dict[str, float]]:
    fs = config.sampling_rate
    harmonics = harmonics or config.num_harmonics
    noise_level = noise_level if noise_level is not None else config.simulation_noise_level

    sample_count = int(fs * duration_s)
    t = np.linspace(0.0, duration_s, sample_count, endpoint=False)
    signal = np.zeros_like(t)
    fundamental = spec.blade_pass_frequency

    for k in range(1, harmonics + 1):
        amplitude = 1.0 / k
        signal += amplitude * np.sin(2 * math.pi * fundamental * k * t)

    if noise_level > 0:
        signal += noise_level * np.random.randn(sample_count)

    metadata = {
        "timestamp": float(sample_count) / fs,
        "rpm": spec.rpm,
        "blades": spec.blades,
        "fundamental_hz": fundamental,
        "harmonics": harmonics,
    }
    return t, signal.astype(np.float32), metadata
