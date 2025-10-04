"""Command-line entry point for the YOLOv8 image sensor pipeline."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import List, Sequence

from .yolov8_person_pipeline import Yolov8PersonCaptionSchema

IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff"}


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
	parser = argparse.ArgumentParser(
		prog="python -m DefHack.sensors.images",
		description=(
			"Run the YOLOv8 person/vehicle detection pipeline on one or more images and "
			"emit SensorReading objects."
		),
	)
	parser.add_argument(
		"sources",
		nargs="+",
		type=Path,
		help="Image files or directories containing images to analyse.",
	)
	parser.add_argument(
		"--weights",
		default=Yolov8PersonCaptionSchema.DEFAULT_WEIGHTS,
		help=f"Ultralytics weights identifier or path (default: {Yolov8PersonCaptionSchema.DEFAULT_WEIGHTS}).",
	)
	parser.add_argument(
		"--confidence",
		type=float,
		default=0.25,
		help="Detection confidence threshold between 0 and 1 (default: 0.25).",
	)
	parser.add_argument(
		"--mgrs",
		default="UNKNOWN",
		help="MGRS string associated with the imagery (default: UNKNOWN).",
	)
	parser.add_argument(
		"--sensor-id",
		default="YOLOv8-Pipeline",
		help="Sensor identifier embedded in the SensorReading outputs.",
	)
	parser.add_argument(
		"--observer",
		default="YOLOv8 Inference",
		help="Observer signature embedded in the SensorReading outputs.",
	)
	parser.add_argument(
		"--device",
		default=None,
		help="Explicit device to run inference on (e.g. 'cpu' or 'cuda').",
	)
	parser.add_argument(
		"--caption-model",
		default=Yolov8PersonCaptionSchema.DEFAULT_CAPTION_MODEL,
		help="open_clip model spec used for caption retrieval.",
	)
	parser.add_argument(
		"--caption-top-k",
		type=int,
		default=1,
		help="Number of corpus entries to include in each caption (default: 1).",
	)
	parser.add_argument(
		"--caption-corpus",
		type=Path,
		default=Path("src/bag_of_words.txt"),
		help="Path to the caption corpus text file (default: src/bag_of_words.txt).",
	)
	parser.add_argument(
		"--no-caption",
		dest="caption",
		action="store_false",
		help="Disable caption generation.",
	)
	parser.add_argument("--caption", dest="caption", action="store_true", help=argparse.SUPPRESS)
	parser.set_defaults(caption=True)
	parser.add_argument(
		"--readings-json",
		type=Path,
		help="Optional path to write SensorReading objects as JSON.",
	)
	parser.add_argument(
		"--no-summary",
		dest="summary",
		action="store_false",
		help="Suppress console summary output.",
	)
	parser.add_argument("--summary", dest="summary", action="store_true", help=argparse.SUPPRESS)
	parser.set_defaults(summary=True)
	return parser.parse_args(list(argv))


def _resolve_image_paths(sources: Sequence[Path]) -> List[Path]:
	images: List[Path] = []
	missing: List[Path] = []

	for source in sources:
		expanded = source.expanduser()
		path = expanded.resolve()
		if not path.exists():
			missing.append(path)
			continue
		if path.is_file():
			if path.suffix.lower() in IMAGE_SUFFIXES:
				images.append(path)
			else:
				print(f"[warning] Skipping unsupported file: {path}", file=sys.stderr)
			continue
		for child in sorted(path.iterdir()):
			if child.is_file() and child.suffix.lower() in IMAGE_SUFFIXES:
				images.append(child)

	if missing:
		missing_str = ", ".join(str(item) for item in missing)
		raise FileNotFoundError(f"No such file or directory: {missing_str}")

	return images


def _summarise_detections(image_path: Path, schemas: Sequence[Yolov8PersonCaptionSchema]) -> None:
	if not schemas:
		print(f"{image_path.name}: no detections above threshold.")
		return

	print(f"{image_path.name}: {len(schemas)} detection(s)")
	for schema in schemas:
		caption = f" | {schema.caption}" if schema.caption else ""
		print(
			f"  [{schema.detection_index}] {schema.label} "
			f"(confidence {schema.detection_confidence:.2f}){caption}"
		)


def _write_sensor_readings_json(destination: Path, readings) -> None:
	destination = destination.expanduser()
	destination.parent.mkdir(parents=True, exist_ok=True)
	payload = [reading.model_dump() for reading in readings]
	with destination.open("w", encoding="utf-8") as fp:
		json.dump(payload, fp, indent=2, default=str)
	print(f"Sensor readings written to {destination}")


def main(argv: Sequence[str] | None = None) -> int:
	args = parse_args(sys.argv[1:] if argv is None else argv)

	try:
		image_paths = _resolve_image_paths(args.sources)
	except FileNotFoundError as exc:
		print(f"[error] {exc}", file=sys.stderr)
		return 2

	if not image_paths:
		joined_sources = ", ".join(str(src) for src in args.sources)
		print(f"[warning] No supported image files found in: {joined_sources}")
		return 0

	exit_code = 0
	all_readings = []

	for image_path in image_paths:
		try:
			readings, schemas, _ = Yolov8PersonCaptionSchema.analyze_image(
				image_path=image_path,
				mgrs=args.mgrs,
				sensor_id=args.sensor_id,
				observer_signature=args.observer,
				weights=args.weights,
				caption_model=args.caption_model,
				confidence=args.confidence,
				caption=args.caption,
				device=args.device,
				caption_corpus=args.caption_corpus,
				caption_top_k=args.caption_top_k,
			)
		except Exception as exc:  # pragma: no cover - surfaces runtime issues for CLI users
			print(f"[error] Failed to analyse {image_path}: {exc}", file=sys.stderr)
			exit_code = 1
			continue

		all_readings.extend(readings)
		if args.summary:
			_summarise_detections(image_path, schemas)

	if args.readings_json and all_readings:
		_write_sensor_readings_json(args.readings_json, all_readings)

	return exit_code


if __name__ == "__main__":
	raise SystemExit(main())