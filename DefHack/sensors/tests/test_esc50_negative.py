from pathlib import Path
from typing import Optional

import pytest

from DefHack.sensors.audio.evaluate_dataset import evaluate_dataset

ESC50_CANDIDATES = [
    Path("datasets/ESC-50/ESC-50-master/audio"),
    Path("ESC-50/audio"),
]

def _find_esc50_root() -> Optional[Path]:
    for candidate in ESC50_CANDIDATES:
        if candidate.exists():
            return candidate
    return None


ESC50_ROOT = _find_esc50_root()


@pytest.mark.skipif(
    ESC50_ROOT is None,
    reason="ESC-50 dataset not available locally",
)
def test_esc50_background_audio_produces_no_detections():
    assert ESC50_ROOT is not None
    records = evaluate_dataset(
        ESC50_ROOT,
        max_files=20,
        overrides={
            "prominence_ratio": "1000",
        },
        save_reports=False,
        show_progress=False,
        shuffle_seed=123,
    )

    assert records, "Expected at least one sample from ESC-50"
    assert all(
        not record.detected for record in records
    ), "ESC-50 should not trigger drone detections"
