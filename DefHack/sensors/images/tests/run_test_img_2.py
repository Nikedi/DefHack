"""Convenience script to exercise the image pipeline on ``test_img_2.jpg``.

Run with:

    uv run python -m DefHack.sensors.images.tests.run_test_img_2

It will execute the soldier-recognition pipeline, convert the result into a
``SensorReading`` and print a human-friendly summary to the console. It also
renders the segmentation masks on top of the original image for quick visual
assurance.
"""

from __future__ import annotations

import base64
import json
import sys
from datetime import datetime
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

PROJECT_ROOT = Path(__file__).resolve().parents[4]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from DefHack.sensors import settings
from DefHack.sensors.images import soldier_recognition_pipeline


_COLOR_PALETTE = [
    (255, 99, 71, 110),     # tomato
    (72, 209, 204, 110),    # medium turquoise
    (123, 104, 238, 110),   # medium slate blue
    (255, 215, 0, 110),     # gold
    (255, 105, 180, 110),   # hot pink
    (60, 179, 113, 110),    # medium sea green
]


def _format_detection(det: dict, index: int) -> dict:
    """Return a serialisable summary of a detection."""
    summary = {
        "bounding_box": det.get("bounding_box"),
        "confidence": det.get("confidence"),
        "classification": det.get("classification", {}),
    }
    mask = det.get("mask", "")
    if mask:
        summary["mask_preview"] = mask[:48] + ("…" if len(mask) > 48 else "")
        summary["overlay_color"] = _rgba_to_hex(_color_for_index(index))
    return summary


def _color_for_index(index: int) -> tuple[int, int, int, int]:
    return _COLOR_PALETTE[index % len(_COLOR_PALETTE)]


def _rgba_to_hex(color: tuple[int, int, int, int]) -> str:
    r, g, b, _ = color
    return f"#{r:02X}{g:02X}{b:02X}"


def _decode_mask(mask_str: str, expected_shape: tuple[int, int]) -> np.ndarray:
    header, data = mask_str.split(":", 1)
    h, w = map(int, header.split("x"))
    decoded = np.frombuffer(base64.b64decode(data), dtype=np.uint8)
    mask = np.unpackbits(decoded)[: h * w].reshape((h, w)).astype(np.uint8)
    if (h, w) != expected_shape:
        target_h, target_w = expected_shape
        copy_h = min(target_h, h)
        copy_w = min(target_w, w)
        padded = np.zeros((target_h, target_w), dtype=np.uint8)
        padded[:copy_h, :copy_w] = mask[:copy_h, :copy_w]
        return padded
    return mask


def _render_segmentation_overlay(image_path: Path, detections: list[dict]) -> Path:
    base_image = Image.open(image_path).convert("RGBA")
    overlay = Image.new("RGBA", base_image.size, (0, 0, 0, 0))
    expected_shape = (base_image.height, base_image.width)
    active_indices: list[int] = []

    for idx, det in enumerate(detections):
        mask_str = det.get("mask")
        if not mask_str:
            continue
        mask = _decode_mask(mask_str, expected_shape)
        if mask.sum() == 0:
            continue
        mask_img = Image.fromarray(mask * 255)
        color = _color_for_index(idx)
        color_img = Image.new("RGBA", base_image.size, color)
        overlay = Image.composite(color_img, overlay, mask_img)
        active_indices.append(idx)

    combined = Image.alpha_composite(base_image, overlay)
    draw = ImageDraw.Draw(combined)
    for idx in active_indices:
        bbox = detections[idx].get("bounding_box")
        if not bbox or len(bbox) != 4:
            continue
        color_rgb = _color_for_index(idx)[:3]
        draw.rectangle(bbox, outline=color_rgb, width=3)

    output_path = image_path.with_name(f"{image_path.stem}_overlay.png")
    combined.save(output_path)
    try:
        combined.show()
    except Exception as exc:  # pragma: no cover - best-effort preview
        print(f"(overlay preview unavailable: {exc})")
    finally:
        base_image.close()

    return output_path


def main() -> None:
    image_path = Path(__file__).with_name("test_img_1.jpg")
    if not image_path.exists():
        raise FileNotFoundError(f"Expected image not found: {image_path}")

    print("\n=== Running soldier recognition pipeline on test_img_2.jpg ===\n")
    result = soldier_recognition_pipeline(
        str(image_path),
        Timestamp=datetime.utcnow().isoformat() + "Z",
        Place="Test Range",
        Produced_by="dev-script",
    )

    overlay_path = _render_segmentation_overlay(image_path, result.detections)

    reading = result.to_dict(
        mgrs="32VNM1234567890",
        what="soldier",
        sensor_id="dev-script",
        observer_signature="Sensor Dev",
    )

    print("SensorReading summary:\n")
    print(reading.model_dump_json(indent=2))

    print(f"\nSegmentation overlay saved to: {overlay_path}")

    print("\nDetections ({} total):\n".format(len(result.detections)))
    for idx, detection in enumerate(result.detections):
        summary = _format_detection(detection, idx)
        print(f"Detection {idx + 1}:")
        print(json.dumps(summary, indent=2))
        print()

    print("Backends used:")
    print(
        json.dumps(
            {
                "detection_backend": settings.settings.detection_backend,
                "segmentation_backend": settings.settings.segmentation_backend,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
