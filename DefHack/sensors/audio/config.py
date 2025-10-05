from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, Mapping, MutableMapping


_DEFAULT_CONFIG_PATH = Path(__file__).with_name("config.yaml")


def _coerce_value(value: str) -> Any:
    lowered = value.lower()
    if lowered in {"true", "false"}:
        return lowered == "true"
    try:
        if "." in value or "e" in lowered:
            return float(value)
        return int(value)
    except ValueError:
        return value


def _parse_simple_yaml(text: str) -> Dict[str, Any]:
    data: Dict[str, Any] = {}
    for raw in text.splitlines():
        stripped = raw.split("#", 1)[0].strip()
        if not stripped or ":" not in stripped:
            continue
        key, raw_value = stripped.split(":", 1)
        key = key.strip()
        value = _coerce_value(raw_value.strip())
        data[key] = value
    return data


@dataclass(frozen=True)
class AcousticConfig:
    sampling_rate: int = 44_100
    fft_size: int = 4_096
    min_bpf_hz: float = 40.0
    max_bpf_hz: float = 2_500.0
    num_harmonics: int = 6
    prominence_ratio: float = 6.0
    noise_floor_db: float = -42.0
    window: str = "hann"
    default_rpm: float = 4_800.0
    default_blades: int = 4
    simulation_noise_level: float = 0.02

    def to_dict(self) -> Dict[str, Any]:
        return {
            "sampling_rate": self.sampling_rate,
            "fft_size": self.fft_size,
            "min_bpf_hz": self.min_bpf_hz,
            "max_bpf_hz": self.max_bpf_hz,
            "num_harmonics": self.num_harmonics,
            "prominence_ratio": self.prominence_ratio,
            "noise_floor_db": self.noise_floor_db,
            "window": self.window,
            "default_rpm": self.default_rpm,
            "default_blades": self.default_blades,
            "simulation_noise_level": self.simulation_noise_level,
        }


def load_config(path: str | Path | None = None, overrides: Mapping[str, Any] | None = None) -> AcousticConfig:
    config_path = Path(path) if path else _DEFAULT_CONFIG_PATH
    if config_path.exists():
        text = config_path.read_text(encoding="utf-8")
        payload = _parse_simple_yaml(text)
    else:
        payload = {}

    if overrides:
        for key, value in overrides.items():
            if isinstance(value, str):
                payload[key] = _coerce_value(value)
            else:
                payload[key] = value

    return AcousticConfig(**{**AcousticConfig().to_dict(), **payload})


def update_config_file(path: str | Path, updates: Mapping[str, Any]) -> None:
    existing = load_config(path)
    merged = {**existing.to_dict(), **updates}
    lines: Iterable[str] = (f"{key}: {value}" for key, value in merged.items())
    Path(path).write_text("\n".join(lines) + "\n", encoding="utf-8")
