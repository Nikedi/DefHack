
"""Shared pytest fixtures for the image pipeline tests."""

import numpy as np
import pytest


@pytest.fixture
def dummy_image() -> np.ndarray:
    rng = np.random.default_rng(42)
    image = rng.integers(0, 80, size=(128, 128, 3), dtype=np.uint8)
    image[32:96, 48:80, :] = 220  # bright rectangle representing a soldier
    return image
