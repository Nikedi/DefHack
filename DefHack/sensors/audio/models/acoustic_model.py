from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Dict


@dataclass(frozen=True)
class RotorSpecification:
    rpm: float
    blades: int
    radius_m: float
    air_density: float = 1.2041  # kg/m^3 at ~20°C
    speed_of_sound: float = 343.0  # m/s

    @property
    def blade_pass_frequency(self) -> float:
        return blade_pass_frequency(self.rpm, self.blades)

    @property
    def tip_speed(self) -> float:
        return tip_speed(self.rpm, self.radius_m)

    @property
    def tip_mach_number(self) -> float:
        return tip_mach_number(self.rpm, self.radius_m, self.speed_of_sound)


def blade_pass_frequency(rpm: float, blades: int) -> float:
    return float(blades) * float(rpm) / 60.0


def tip_speed(rpm: float, radius_m: float) -> float:
    return 2.0 * math.pi * (rpm / 60.0) * radius_m


def tip_mach_number(rpm: float, radius_m: float, speed_of_sound: float = 343.0) -> float:
    return tip_speed(rpm, radius_m) / speed_of_sound


def sound_pressure_level(spec: RotorSpecification, reference_pressure: float = 20e-6) -> float:
    """Return a crude broadband SPL estimate based on tip Mach number."""
    mach = spec.tip_mach_number
    if mach <= 0:
        return -math.inf
    # Empirical log fit: L_p ≈ 50 + 40 log10(M)
    base = 50.0 + 40.0 * math.log10(max(mach, 1e-6))
    return base + 20 * math.log10(spec.tip_speed / reference_pressure)


def expected_harmonic_frequencies(spec: RotorSpecification, count: int) -> Dict[int, float]:
    return {k: spec.blade_pass_frequency * k for k in range(1, count + 1)}
