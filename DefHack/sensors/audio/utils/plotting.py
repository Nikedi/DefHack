from __future__ import annotations

from typing import Iterable, Optional

import numpy as np

try:  # pragma: no cover - optional dependency
    import matplotlib.pyplot as plt
except ImportError:  # pragma: no cover - gracefully degrade
    plt = None


def plot_spectrum(freq: np.ndarray, magnitude: np.ndarray, *, title: str = "Spectrum") -> None:
    if plt is None:
        raise RuntimeError("matplotlib is not installed; plotting is unavailable")
    plt.figure(figsize=(10, 4))
    plt.plot(freq, magnitude)
    plt.xlabel("Frequency [Hz]")
    plt.ylabel("Amplitude")
    plt.title(title)
    plt.grid(True)
    plt.tight_layout()
    plt.show()


def stem_plot(freqs: Iterable[float], values: Iterable[float], *, title: str = "BPF Harmonics") -> None:
    if plt is None:
        raise RuntimeError("matplotlib is not installed; plotting is unavailable")
    freqs_list = list(freqs)
    values_list = list(values)
    plt.figure(figsize=(8, 4))
    plt.stem(freqs_list, values_list, use_line_collection=True)
    plt.xlabel("Frequency [Hz]")
    plt.ylabel("Amplitude [dB]")
    plt.title(title)
    plt.grid(True)
    plt.tight_layout()
    plt.show()
