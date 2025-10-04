"""Run YOLOv8n inference on images inside ``src/img`` using default Ultralytics weights.

This script leverages the Ultralytics `YOLO` API to download (if required) and
load the ``yolov8n.pt`` checkpoint, perform inference on a directory of images,
and optionally display and/or persist the annotated outputs.
"""
from __future__ import annotations

import argparse
import json
import sys
import textwrap
from pathlib import Path
from typing import Iterable, List

import cv2
import matplotlib.pyplot as plt
import torch

from yolov8_person_pipeline import Yolov8PersonCaptionSchema

IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff"}


def parse_args(argv: List[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="run_inference_v8.py",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=textwrap.dedent(
            """
            Run Ultralytics YOLOv8 inference on a directory of images using the
            default ``yolov8n.pt`` weights (downloaded automatically).
            """
        ),
    )
    parser.add_argument(
        "--weights",
        type=str,
        default="yolov8n.pt",
        help="Weights identifier or path accepted by Ultralytics YOLO (default: yolov8n.pt).",
    )
    parser.add_argument(
        "--image-dir",
        type=Path,
        default=Path("src/img"),
        help="Directory containing images to process.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("src/predictions_v8"),
        help="Directory where annotated images will be written.",
    )
    parser.add_argument(
        "--confidence",
        type=float,
        default=0.25,
        help="Confidence threshold for detections (0-1).",
    )
    parser.add_argument(
        "--show",
        action="store_true",
        help="Display each annotated image using matplotlib.",
    )
    parser.add_argument(
        "--caption",
        dest="caption",
        action="store_true",
        default=True,
        help="Generate CLIP retrieval captions for each detected person (default: enabled).",
    )
    parser.add_argument(
        "--no-caption",
        dest="caption",
        action="store_false",
        help="Disable caption generation.",
    )
    parser.add_argument(
        "--caption-model",
        type=str,
        default="MobileCLIP-S1::datacompdr",
        help=(
            "Model spec for open_clip retrieval (use 'model::pretrained' or an hf-hub reference)."
        ),
    )
    parser.add_argument(
        "--caption-top-k",
        type=int,
        default=1,
        help="Number of corpus entries to include in each caption (top-k by CLIP similarity).",
    )
    parser.add_argument(
        "--caption-corpus",
        type=Path,
        default=Path("src/bag_of_words.txt"),
        help="Path to the corpus file (one phrase per line) used for CLIP retrieval.",
    )
    parser.add_argument(
        "--mgrs",
        type=str,
        default="UNKNOWN",
        help="MGRS string associated with the image set (uppercased automatically).",
    )
    parser.add_argument(
        "--sensor-id",
        type=str,
        default="YOLOv8-Pipeline",
        help="Sensor identifier to embed in generated SensorReading objects.",
    )
    parser.add_argument(
        "--observer",
        dest="observer_signature",
        type=str,
        default="YOLOv8 Inference",
        help="Observer signature used for SensorReading output.",
    )
    parser.add_argument(
        "--readings-json",
        type=Path,
        default=None,
        help="Optional path to write generated SensorReading objects as JSON.",
    )
    return parser.parse_args(argv)


def iter_image_files(image_dir: Path) -> Iterable[Path]:
    if not image_dir.exists():
        raise FileNotFoundError(f"Image directory not found: {image_dir}")

    for path in sorted(image_dir.iterdir()):
        if path.is_file() and path.suffix.lower() in IMAGE_SUFFIXES:
            yield path


def annotate_and_save(result, image_path: Path, output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    annotated = result.plot()  # returns BGR numpy array
    output_path = output_dir / f"{image_path.stem}_pred{image_path.suffix}"
    cv2.imwrite(str(output_path), annotated)
    return output_path


def display_image(image_path: Path) -> None:
    image = cv2.imread(str(image_path))
    if image is None:
        print(f"[warning] Unable to read image for display: {image_path}")
        return

    rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    plt.figure(figsize=(10, 8))
    plt.imshow(rgb_image)
    plt.title(image_path.name)
    plt.axis("off")
    plt.tight_layout()
    plt.show()


def summarize_result(result, image_path: Path) -> None:
    boxes = getattr(result, "boxes", None)
    if boxes is None or len(boxes) == 0:
        print(f"{image_path.name}: No detections above threshold.")
        return

    names = result.names
    summary_items = []
    for cls_id, conf in zip(boxes.cls.tolist(), boxes.conf.tolist()):
        cls_idx = int(cls_id)
        if isinstance(names, dict):
            name = names.get(cls_idx, str(cls_idx))
        elif isinstance(names, list):
            name = names[cls_idx] if 0 <= cls_idx < len(names) else str(cls_idx)
        else:
            name = str(cls_idx)
        summary_items.append(f"{name} ({conf:.2f})")

    print(f"{image_path.name}: {', '.join(summary_items)}")


def main(argv: List[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)

    try:
        image_paths = list(iter_image_files(args.image_dir))
    except FileNotFoundError as exc:
        print(f"[error] {exc}")
        return 1

    if not image_paths:
        print(
            f"[warning] No images with extensions {sorted(IMAGE_SUFFIXES)} found in"
            f" {args.image_dir.resolve()}"
        )
        return 0

    device = "cuda" if torch.cuda.is_available() else "cpu"
    all_readings = []

    print(f"Running YOLOv8 inference with weights: {args.weights}")
    print(f"Processing {len(image_paths)} image(s) from {args.image_dir.resolve()}\n")

    for image_path in image_paths:
        readings, schemas, result = Yolov8PersonCaptionSchema.analyze_image(
            image_path=image_path,
            mgrs=args.mgrs,
            sensor_id=args.sensor_id,
            observer_signature=args.observer_signature,
            weights=args.weights,
            caption_model=args.caption_model,
            confidence=args.confidence,
            caption=args.caption,
            device=device,
            caption_corpus=args.caption_corpus,
            caption_top_k=args.caption_top_k,
        )
        all_readings.extend(readings)

        if result is None:
            print(f"{image_path.name}: No results returned by the model.")
            continue

        summarize_result(result, image_path)
        output_path = annotate_and_save(result, image_path, args.output_dir)
        print(f"  ↳ Saved annotated image to {output_path}")

        if args.caption:
            if schemas:
                for schema in schemas:
                    if schema.caption:
                        print(
                            f"    caption[{schema.detection_index}] ({schema.label}): {schema.caption}"
                        )
                    else:
                        print(
                            f"    detection[{schema.detection_index}] ({schema.label}): confidence={schema.detection_confidence:.2f}"
                        )
            else:
                print("    No target detections to caption.")

        if args.show:
            display_image(output_path)

    print("\nInference complete.")
    if not args.show:
        print("Use --show to visualize the annotated detections interactively.")

    if args.readings_json and all_readings:
        args.readings_json.parent.mkdir(parents=True, exist_ok=True)
        with args.readings_json.open("w", encoding="utf-8") as fp:
            json.dump([reading.model_dump() for reading in all_readings], fp, indent=2, default=str)
        print(f"Sensor readings written to {args.readings_json}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
