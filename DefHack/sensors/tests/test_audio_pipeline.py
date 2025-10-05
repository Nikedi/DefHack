from __future__ import annotations

import numpy as np

from DefHack.sensors.SensorSchema import SensorSchema
from DefHack.sensors.audio import analyze_audio
from DefHack.sensors.audio.models import blade_pass_frequency
from DefHack.sensors.audio.schemas import AcousticDroneSchema


def test_simulated_rotor_detection() -> None:
    rpm = 4_200
    blades = 4
    schema = SensorSchema.from_sensor(
        None,
        algorithm="acoustic_drone_bpf",
        rpm=rpm,
        blades=blades,
        duration_s=2.0,
    )

    assert isinstance(schema, AcousticDroneSchema)
    fundamental = schema.metadata.get("fundamental_hz")
    assert fundamental is not None
    expected = blade_pass_frequency(rpm, blades)
    assert abs(fundamental - expected) < expected * 0.05
    assert schema.metadata.get("confidence_pct", 0) >= 40

    observation = schema.to_sensor_message(observer_signature="TestHarness")
    assert "rotor" in observation.what.lower()
    assert observation.confidence >= 40


def test_silence_returns_no_detection() -> None:
    silence = np.zeros(4_096, dtype=np.float32)
    schema = analyze_audio(
        silence,
        sample_rate=44_100,
        rpm=3_600,
        blades=3,
    )

    assert schema.metadata.get("fundamental_hz") is None
    assert schema.metadata.get("confidence_pct") == 0
    observation = schema.to_sensor_message()
    assert "no rotor" in observation.what.lower()
