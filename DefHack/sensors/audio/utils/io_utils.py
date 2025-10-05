from __future__ import annotations

import wave
from pathlib import Path
from typing import Tuple

import numpy as np


_INT16_MAX = float(np.iinfo(np.int16).max)


def load_wav(path: str | Path) -> Tuple[float, np.ndarray]:
    file_path = Path(path)
    with wave.open(str(file_path), "rb") as wav_file:
        sample_rate = wav_file.getframerate()
        frame_count = wav_file.getnframes()
        channels = wav_file.getnchannels()
        frames = wav_file.readframes(frame_count)
        dtype = np.int16 if wav_file.getsampwidth() == 2 else np.int32
        audio = np.frombuffer(frames, dtype=dtype).astype(np.float32)
        if channels > 1:
            audio = audio.reshape(-1, channels).mean(axis=1)
        if dtype == np.int16:
            audio /= _INT16_MAX
        else:
            audio /= float(np.iinfo(dtype).max)
    return float(sample_rate), audio


def write_wav(path: str | Path, sample_rate: float, signal: np.ndarray) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    int_signal = np.clip(signal, -1.0, 1.0) * _INT16_MAX
    int_signal = int_signal.astype(np.int16)
    with wave.open(str(out_path), "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(int(sample_rate))
        wav_file.writeframes(int_signal.tobytes())
