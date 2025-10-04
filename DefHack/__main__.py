"""Camera-driven YOLOv8 ingestion loop.

This module captures frames from the local camera (or a supplied list of test
images), runs the :mod:`DefHack.sensors.images.yolov8_person_pipeline`
inference, and attempts to push each resulting sensor observation to a remote
ingest endpoint. Failed deliveries are persisted locally so they can be retried
on the next iteration.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, List, Optional, Sequence

import cv2
from urllib import error, request

from .sensors.images.camera import CameraWorker, ensure_folder
from .sensors.images.yolov8_person_pipeline import Yolov8PersonCaptionSchema
from .sensors.SensorSchema import SensorObservationIn


DEFAULT_API_URL = "http://localhost:8080/ingest/sensor"
DEFAULT_API_KEY = "583C55345736D7218355BCB51AA47"
DEFAULT_SAVE_FOLDER = Path(__file__).parent / "sensors" / "images" / "current_image"
DEFAULT_BACKLOG_PATH = Path(__file__).parent / "sensor_backlog.json"


@dataclass
class AppConfig:
	interval: float
	mgrs: str
	sensor_id: str
	unit: Optional[str]
	observer_signature: str
	api_url: str
	api_key: Optional[str]
	backlog_file: Path
	save_folder: Path
	source: int
	test_images: Optional[List[Path]]
	iterations: Optional[int]
	weights: Optional[str]
	caption_model: Optional[str]
	caption: bool
	caption_top_k: int
	confidence: float
	device: Optional[str]
	caption_corpus: Optional[Path]
	image_history: int
	http_timeout: float


def parse_args(argv: Sequence[str]) -> AppConfig:
	parser = argparse.ArgumentParser(description="Continuously capture images and post detections.")
	parser.add_argument("--interval", type=float, default=10.0, help="Seconds between captures (default: 10)")
	parser.add_argument(
		"--mgrs",
		default="UNKNOWN",
		help="MGRS location coded into sensor readings (default: UNKNOWN)",
	)
	parser.add_argument(
		"--sensor-id",
		default="YOLOv8-Pipeline",
		help="Sensor identifier reported to the API (default: YOLOv8-Pipeline)",
	)
	parser.add_argument(
		"--unit",
		default=None,
		help="Unit label for the sensor readings (default: use pipeline-provided value)",
	)
	parser.add_argument(
		"--observer-signature",
		default="YOLOv8 Inference",
		help="Observer signature included with each reading (default: YOLOv8 Inference)",
	)
	parser.add_argument("--api-url", default=DEFAULT_API_URL, help="Target ingestion endpoint URL")
	parser.add_argument("--api-key", default=DEFAULT_API_KEY, help="API key for the ingestion endpoint")
	parser.add_argument("--backlog-file", type=Path, default=DEFAULT_BACKLOG_PATH, help="Path to persist undelivered sensor readings")
	parser.add_argument("--save-folder", type=Path, default=DEFAULT_SAVE_FOLDER, help="Directory where captured images are stored")
	parser.add_argument("--source", type=int, default=0, help="Camera device index for OpenCV")
	parser.add_argument("--test-images", type=Path, nargs="*", default=None, help="Optional list of images to replay instead of using a live camera")
	parser.add_argument("--iterations", type=int, default=None, help="Stop after this many iterations (default: run forever)")
	parser.add_argument("--weights", default=None, help="Override YOLO weights path")
	parser.add_argument("--caption-model", default=None, help="Override caption model identifier")
	parser.add_argument("--no-caption", action="store_true", help="Disable caption retrieval to speed up inference")
	parser.add_argument("--caption-top-k", type=int, default=1, help="How many captions to retrieve per detection (default: 1)")
	parser.add_argument("--confidence", type=float, default=0.25, help="Minimum detection confidence for YOLO (default: 0.25)")
	parser.add_argument("--device", default=None, help="Preferred torch device (e.g., 'cuda' or 'cpu')")
	parser.add_argument("--caption-corpus", type=Path, default=None, help="Optional phrase corpus for CLIP retrieval")
	parser.add_argument("--image-history", type=int, default=5, help="How many captured images to retain on disk (default: 5)")
	parser.add_argument("--http-timeout", type=float, default=5.0, help="Seconds before HTTP POST attempts time out (default: 5)")
	args = parser.parse_args(argv)

	return AppConfig(
		interval=max(1.0, args.interval),
		mgrs=args.mgrs,
		sensor_id=args.sensor_id,
		unit=args.unit or None,
		observer_signature=args.observer_signature,
		api_url=args.api_url,
		api_key=args.api_key or None,
		backlog_file=args.backlog_file.resolve(),
		save_folder=args.save_folder.resolve(),
		source=args.source,
		test_images=[img.resolve() for img in args.test_images] if args.test_images else None,
		iterations=args.iterations,
		weights=args.weights,
		caption_model=args.caption_model,
		caption=not args.no_caption,
		caption_top_k=max(1, args.caption_top_k),
		confidence=max(0.0, min(args.confidence, 1.0)),
		device=args.device,
		caption_corpus=args.caption_corpus.resolve() if args.caption_corpus else None,
		image_history=max(1, args.image_history),
		http_timeout=max(1.0, args.http_timeout),
	)


def _format_timestamp(value: object) -> str:
	if isinstance(value, datetime):
		dt = value
	elif isinstance(value, str):
		try:
			dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
		except ValueError:
			return value
	else:
		dt = datetime.now(timezone.utc)

	if dt.tzinfo is None:
		dt = dt.replace(tzinfo=timezone.utc)
	else:
		dt = dt.astimezone(timezone.utc)

	return dt.isoformat(sep=" ", timespec="microseconds")


def _format_mgrs(value: Optional[str]) -> str:
	if not value:
		return "UNKNOWN"
	cleaned = value.replace(" ", "").upper()
	return cleaned or "UNKNOWN"


def _normalise_what(value: Optional[str]) -> str:
	if not value:
		return ""
	prefix = "TACTICAL:"
	if value.startswith(prefix):
		return value[len(prefix):]
	return value


def _load_backlog(path: Path) -> List[dict[str, object]]:
	if not path.exists():
		return []
	try:
		raw = path.read_text(encoding="utf-8")
		if not raw.strip():
			return []
		data = json.loads(raw)
		if isinstance(data, list):
			return [item for item in data if isinstance(item, dict)]
	except Exception as exc:
		print(f"Warning: failed to read backlog {path}: {exc}")
	return []


def _save_backlog(path: Path, backlog: Sequence[dict[str, object]]) -> None:
	if not backlog:
		if path.exists():
			try:
				path.unlink()
			except Exception:
				pass
		return
	try:
		path.write_text(json.dumps(list(backlog), indent=2), encoding="utf-8")
	except Exception as exc:
		print(f"Warning: failed to persist backlog {path}: {exc}")


def _post_payload(payload: dict[str, object], *, url: str, api_key: Optional[str], timeout: float) -> bool:
	encoded = json.dumps(payload).encode("utf-8")
	req = request.Request(url, data=encoded, method="POST")
	req.add_header("Content-Type", "application/json")
	if api_key:
		req.add_header("X-API-Key", api_key)
	try:
		with request.urlopen(req, timeout=timeout) as resp:
			status = getattr(resp, "status", 200)
			if 200 <= status < 300:
				# Consume response body to avoid resource warnings.
				resp.read()
				return True
			print(f"Server responded with HTTP {status}, will retry later.")
	except error.HTTPError as http_exc:
		print(f"HTTP error posting sensor reading: {http_exc.status} {http_exc.reason}")
	except error.URLError as url_exc:
		print(f"Network error posting sensor reading: {url_exc}")
	except Exception as exc:
		print(f"Unexpected error posting sensor reading: {exc}")
	return False


def _prepare_payloads(
	readings: Iterable[SensorObservationIn],
	*,
	unit_override: Optional[str],
) -> List[dict[str, object]]:
	payloads: List[dict[str, object]] = []
	for reading in readings:
		try:
			payload = reading.model_dump(mode="python")
		except AttributeError:
			payload = reading.dict()  # type: ignore[attr-defined]
		timestamp = _format_timestamp(payload.get("time"))
		amount = payload.get("amount")
		payloads.append(
			{
				"time": timestamp,
				"mgrs": _format_mgrs(payload.get("mgrs")),
				"what": _normalise_what(payload.get("what")),
				"amount": float(amount) if amount is not None else 0.0,
				"confidence": int(payload.get("confidence", 0)),
				"sensor_id": payload.get("sensor_id"),
				"unit": unit_override if unit_override is not None else payload.get("unit"),
				"observer_signature": payload.get("observer_signature"),
				"original_message": payload.get("original_message"),
			}
		)
	return payloads


def _deliver_readings(
	payloads: Sequence[dict[str, object]],
	*,
	backlog_path: Path,
	url: str,
	api_key: Optional[str],
	timeout: float,
) -> None:
	if not payloads and not backlog_path.exists():
		return

	backlog = _load_backlog(backlog_path)
	backlog.extend(payloads)

	remaining: List[dict[str, object]] = []
	delivered = 0

	for payload in backlog:
		if _post_payload(payload, url=url, api_key=api_key, timeout=timeout):
			delivered += 1
			print(f"Delivered reading: {payload.get('what')} @ {payload.get('time')}")
		else:
			remaining.append(payload)

	if remaining:
		print(f"{len(remaining)} readings queued for retry.")
	elif delivered:
		print("Backlog cleared.")

	_save_backlog(backlog_path, remaining)


def _capture_frame(camera: CameraWorker, save_dir: Path) -> Optional[Path]:
	frame = camera.get_latest_frame(timeout=2.0)
	if frame is None:
		print("No frame available from camera.")
		return None

	ensure_folder(str(save_dir))
	timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
	image_path = save_dir / f"capture_{timestamp}.jpg"
	try:
		if not cv2.imwrite(str(image_path), frame):
			print(f"Failed to write image to {image_path}.")
			return None
	except Exception as exc:
		print(f"Error while saving image {image_path}: {exc}")
		return None
	return image_path


def _prune_captures(folder: Path, *, keep: int) -> None:
	if keep < 0:
		return
	if not folder.exists():
		return
	try:
		entries = []
		for item in folder.iterdir():
			if not item.is_file():
				continue
			if not item.name.startswith("capture_"):
				continue
			try:
				mtime = item.stat().st_mtime
			except OSError:
				continue
			entries.append((mtime, item))
		if len(entries) <= keep:
			return
		entries.sort(key=lambda pair: pair[0])
		for _, path in entries[:-keep]:
			try:
				path.unlink()
				print(f"Removed stale capture: {path.name}")
			except Exception:
				pass
	except Exception as exc:
		print(f"Warning: failed to prune captures in {folder}: {exc}")


def _run_inference(image_path: Path, config: AppConfig) -> List[SensorObservationIn]:
	weights = config.weights or Yolov8PersonCaptionSchema.DEFAULT_WEIGHTS
	caption_model = config.caption_model or Yolov8PersonCaptionSchema.DEFAULT_CAPTION_MODEL
	try:
		readings, _, _ = Yolov8PersonCaptionSchema.analyze_image(
			image_path,
			mgrs=config.mgrs,
			sensor_id=config.sensor_id,
			observer_signature=config.observer_signature,
			weights=weights,
			caption_model=caption_model,
			confidence=config.confidence,
			caption=config.caption,
			device=config.device,
			caption_corpus=config.caption_corpus,
			caption_top_k=config.caption_top_k,
		)
		if readings:
			print(f"Detected {len(readings)} target categories from {image_path.name}.")
		else:
			print(f"No relevant detections found in {image_path.name}.")
		return readings
	except Exception as exc:
		print(f"Inference failed for {image_path}: {exc}")
		return []


def main(argv: Sequence[str] | None = None) -> int:
	config = parse_args(argv if argv is not None else sys.argv[1:])

	camera = CameraWorker(src=config.source, test_images=[str(p) for p in config.test_images] if config.test_images else None)
	empty_frame_runs = 0

	try:
		camera.start()
		print("Camera worker started.")
		iteration = 0
		while config.iterations is None or iteration < config.iterations:
			iteration += 1
			print(f"\nIteration {iteration}")
			loop_started = time.time()

			image_path = _capture_frame(camera, config.save_folder)
			if image_path is None:
				empty_frame_runs += 1
				if config.test_images:
					threshold = max(5, len(config.test_images))
					if empty_frame_runs >= threshold:
						print("No more test frames available; ending loop.")
						break
				else:
					if empty_frame_runs >= 1:
						print("No frames captured from camera. Connect a camera or supply --test-images to proceed.")
						break
				time.sleep(1.0)
				continue

			empty_frame_runs = 0
			readings = _run_inference(image_path, config)
			if readings:
				payloads = _prepare_payloads(readings, unit_override=config.unit)
				_deliver_readings(
					payloads,
					backlog_path=config.backlog_file,
					url=config.api_url,
					api_key=config.api_key,
					timeout=config.http_timeout,
				)
			_prune_captures(config.save_folder, keep=config.image_history)

			elapsed = time.time() - loop_started
			sleep_for = max(0.0, config.interval - elapsed)
			if sleep_for:
				time.sleep(sleep_for)

	except KeyboardInterrupt:
		print("Stopping ingestion loop (KeyboardInterrupt).")
	finally:
		camera.stop()
		try:
			if hasattr(cv2, "destroyAllWindows"):
				cv2.destroyAllWindows()
		except cv2.error as exc:  # pragma: no cover - GUI not available on headless envs
			msg = getattr(exc, "msg", str(exc))
			print(f"Skipping destroyAllWindows: {msg}")

	if empty_frame_runs and not config.test_images:
		return 1

	return 0


if __name__ == "__main__":
	raise SystemExit(main())
