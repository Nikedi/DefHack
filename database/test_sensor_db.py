import unittest
import datetime
from sensor_db import insert_observation

class TestObservationInsert(unittest.TestCase):
    def test_insert(self):
        obs_id = insert_observation(
            "Espoo",
            datetime.datetime.now(datetime.timezone.utc),
            3,
            "ok",
            0.85,
            {"sensor": "B2", "weather": "rainy"},
            [0.2, 0.1, 0.4, 0.3, 0.6, 0.5, 0.8, 0.7]
        )
        self.assertIsInstance(obs_id, int)

if __name__ == "__main__":
    unittest.main()