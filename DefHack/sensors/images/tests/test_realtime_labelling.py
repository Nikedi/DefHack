import time
from datetime import datetime, timezone
from pathlib import Path

import pytest

from DefHack.__main__ import AppConfig, _capture_frame, _run_inference
from DefHack.sensors.SensorSchema import SensorObservationIn
from DefHack.sensors.images.camera import CameraWorker, ensure_folder
from DefHack.sensors.images.yolov8_person_pipeline import Yolov8PersonCaptionSchema


@pytest.mark.skipif(not hasattr(CameraWorker, "start"), reason="CameraWorker not available")
def test_realtime_labelling_with_camera_worker(tmp_path, monkeypatch):
    tests_dir = Path(__file__).parent
    sample_images = sorted(tests_dir.glob("test_img_*.jpg"))[:3]
    assert sample_images, "Expected sample images for camera simulation"

    camera = CameraWorker(src=0, test_images=[str(p) for p in sample_images])
    camera.start()
    try:
        frame = None
        for _ in range(10):
            frame = camera.get_latest_frame(timeout=0.5)
            if frame is not None:
                break
            time.sleep(0.05)
        assert frame is not None, "CameraWorker failed to provide a frame"

        save_dir = tmp_path / "captures"
        ensure_folder(str(save_dir))
        captured_path = _capture_frame(camera, save_dir)
        assert captured_path is not None
        assert captured_path.exists()

        analyzed = []

        def fake_analyze(cls, image_path, **kwargs):
            analyzed.append({"image_path": Path(image_path), "kwargs": kwargs})
            reading = SensorObservationIn(
                time=datetime.now(timezone.utc),
                mgrs=kwargs["mgrs"],
                what="person",
                amount=1.0,
                confidence=88,
                sensor_id=kwargs["sensor_id"],
                unit="CamBot",
                observer_signature=kwargs["observer_signature"],
                original_message=None,
            )
            return [reading], ["schema"], {"raw": True}

        monkeypatch.setattr(
            Yolov8PersonCaptionSchema,
            "analyze_image",
            classmethod(fake_analyze),
        )

        config = AppConfig(
            interval=1.0,
            mgrs="32VNM1234567890",
            sensor_id="unit-test-camera",
            unit=None,
            observer_signature="Unit Test",
            api_url="http://localhost",
            api_key=None,
            backlog_file=tmp_path / "backlog.json",
            save_folder=save_dir,
            source=0,
            test_images=None,
            iterations=1,
            weights="mock.pt",
            caption_model="mock-clip",
            caption=True,
            caption_top_k=1,
            confidence=0.4,
            device="cpu",
            caption_corpus=None,
            image_history=2,
            http_timeout=2.0,
        )

        readings = _run_inference(captured_path, config)

        assert analyzed, "Labelling should invoke analyze_image"
        assert analyzed[0]["image_path"] == captured_path
        assert analyzed[0]["kwargs"]["mgrs"] == config.mgrs
        assert len(readings) == 1
        assert readings[0].what == "person"
        assert readings[0].sensor_id == config.sensor_id
    finally:
        camera.stop()
