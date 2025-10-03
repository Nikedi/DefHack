# conftests.py for pipeline tests
import pytest

@pytest.fixture
def dummy_image():
    # Returns a dummy image (could be a numpy array or any placeholder)
    return "dummy_image_data"
