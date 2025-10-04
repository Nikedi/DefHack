import importlib

import numpy as np
import pytest
import torch
from PIL import Image


PIPELINE_MODULE = importlib.import_module("DefHack.sensors.images.yolov8_person_pipeline")
Yolov8PersonCaptionSchema = PIPELINE_MODULE.Yolov8PersonCaptionSchema


class DummyBoxes:
    def __init__(self, cls_tensor: torch.Tensor, conf_tensor: torch.Tensor, xyxy_tensor: torch.Tensor):
        self.cls = cls_tensor
        self.conf = conf_tensor
        self.xyxy = xyxy_tensor

    def __len__(self) -> int:
        return int(self.cls.shape[0])

    def __getitem__(self, item):
        if isinstance(item, torch.Tensor):
            return DummyBoxes(self.cls[item], self.conf[item], self.xyxy[item])
        return DummyBoxes(self.cls[item], self.conf[item], self.xyxy[item])


class DummyResult:
    def __init__(self, boxes: DummyBoxes, names, image: np.ndarray):
        self.boxes = boxes
        self.names = names
        self.orig_img = image

    def plot(self):
        return self.orig_img


class DummyModel:
    def __init__(self, result: DummyResult):
        self._result = result
        self.predict_calls = []

    def predict(self, *, source, conf, verbose, save, device):
        self.predict_calls.append((source, conf, verbose, save, device))
        return [self._result]


@pytest.fixture
def dummy_image_path(tmp_path):
    image_path = tmp_path / "synthetic.jpg"
    Image.fromarray(np.zeros((64, 64, 3), dtype=np.uint8)).save(image_path)
    return image_path


def test_yolov8_pipeline_generates_sensor_readings(monkeypatch, dummy_image_path):
    boxes = DummyBoxes(
        cls_tensor=torch.tensor([0.0, 2.0]),
        conf_tensor=torch.tensor([0.92, 0.87]),
        xyxy_tensor=torch.tensor([[5.0, 5.0, 40.0, 40.0], [10.0, 10.0, 20.0, 20.0]]),
    )
    image = np.zeros((64, 64, 3), dtype=np.uint8)
    result = DummyResult(boxes=boxes, names={0: "person", 2: "cat"}, image=image)
    model = DummyModel(result=result)

    monkeypatch.setattr(PIPELINE_MODULE, "_load_yolo_model", lambda weights, device: model)

    captions_seen = {}

    def fake_retrieve_captions(crops, detections, *, model_id, device, corpus_path, top_k):
        captions_seen["args"] = {
            "model_id": model_id,
            "device": device,
            "corpus_path": corpus_path,
            "top_k": top_k,
            "num_crops": len(crops),
            "num_detections": len(detections),
        }
        assert len(crops) == len(detections) == 1
        return ["test-caption"]

    monkeypatch.setattr(PIPELINE_MODULE, "_retrieve_captions", fake_retrieve_captions)

    readings, schemas, raw_result = Yolov8PersonCaptionSchema.analyze_image(
        dummy_image_path,
        mgrs="32V NM 7654",
        sensor_id="unit-test-sensor",
        observer_signature="Observer Alpha",
        weights="dummy.pt",
        caption_model="dummy::model",
        confidence=0.5,
        caption=True,
        caption_corpus=None,
    )

    assert len(readings) == 1
    assert len(schemas) == 1

    schema = schemas[0]
    reading = readings[0]

    assert schema.label == "person"
    assert schema.caption == "test-caption"
    assert schema.detection_index == 1
    assert pytest.approx(schema.detection_confidence, rel=1e-6) == 0.92
    assert schema.bbox == (5.0, 5.0, 40.0, 40.0)

    assert reading.mgrs == "32VNM7654"
    assert reading.sensor_id == "unit-test-sensor"
    assert reading.observer_signature == "Observer Alpha"
    assert reading.amount == 1.0
    assert reading.confidence == 92

    assert raw_result.boxes.cls.tolist() == [0.0]
    assert raw_result.boxes.conf.tolist() == pytest.approx([0.92], rel=1e-6)

    assert captions_seen["args"]["model_id"] == "dummy::model"
    assert captions_seen["args"]["corpus_path"] is None
    assert captions_seen["args"]["num_crops"] == 1
    assert captions_seen["args"]["num_detections"] == 1
    assert captions_seen["args"]["top_k"] == 1

    assert model.predict_calls
    source_path, conf, verbose, save, device = model.predict_calls[0]
    assert source_path == str(dummy_image_path)
    assert conf == 0.5
    assert verbose is False
    assert save is False
    assert device in {"cpu", "cuda"}