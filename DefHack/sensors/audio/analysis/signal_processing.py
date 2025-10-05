from __future__ import annotations

import numpy as np


_WINDOW_BUILDERS = {
    "hann": np.hanning,
    "hamming": np.hamming,
    "blackman": np.blackman,
}


def _resolve_window(name: str, size: int) -> np.ndarray:
    func = _WINDOW_BUILDERS.get(name.lower())
    if func is None:
        return np.ones(size)
    return func(size)


def compute_fft(signal: np.ndarray, fs: float, *, fft_size: int, window: str) -> tuple[np.ndarray, np.ndarray]:
    if fft_size < len(signal):
        trimmed = signal[:fft_size]
    elif fft_size > len(signal):
        padded = np.zeros(fft_size, dtype=signal.dtype)
        padded[: len(signal)] = signal
        trimmed = padded
    else:
        trimmed = signal

    win = _resolve_window(window, len(trimmed))
    windowed = trimmed * win
    spectrum = np.fft.rfft(windowed)
    freq = np.fft.rfftfreq(len(windowed), 1.0 / fs)
    magnitude = np.abs(spectrum) / (len(windowed) / 2.0)
    return freq, magnitude


def amplitude_to_db(values: np.ndarray, floor_db: float = -120.0) -> np.ndarray:
    ref = np.maximum(values, 1e-12)
    db = 20.0 * np.log10(ref)
    return np.maximum(db, floor_db)


def estimate_noise_floor(db_spectrum: np.ndarray) -> float:
    # Median as noise approximation
    return float(np.median(db_spectrum))
