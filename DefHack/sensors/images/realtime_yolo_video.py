"""Realtime YOLOv8 labelling for prerecorded video footage.

This script streams frames from a video file through an Ultralytics YOLO model,
annotates detections directly on the frames, and optionally mirrors the output
in a window and/or saves it to disk. CLIP captioning is intentionally omitted so
that only raw YOLO detections are produced, keeping latency low.
"""
from __future__ import annotations

import argparse
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional, Sequence

import cv2
import torch
from ultralytics import YOLO

from .yolov8_person_pipeline import Yolov8PersonCaptionSchema


@dataclass
class VideoSummary:
    total_frames: int = 0
    total_detections: int = 0
    avg_fps: float = 0.0


def _default_weights() -> str:
    """Resolve a sensible default weights path without requiring downloads."""

    candidate = Yolov8PersonCaptionSchema.DEFAULT_WEIGHTS
    module_path = Path(__file__).resolve()
    search_names = [candidate, "yolov8n.pt", "yolov8n-finetune.pt"]
    search_locations = [Path.cwd()] + list(module_path.parents)

    for name in search_names:
        for location in search_locations:
            resolved = (location / name).expanduser()
            if resolved.exists():
                return str(resolved)

    # Fall back to the original identifier so Ultralytics can attempt download.
    return candidate


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="python -m DefHack.sensors.images.realtime_yolo_video",
        description="Run YOLOv8 detection in realtime on a video file",
    )
    parser.add_argument("video", type=Path, help="Path to the video file to analyse")
    parser.add_argument(
        "--weights",
        type=str,
    default=_default_weights(),
    help="Ultralytics weights identifier or path (default: local yolov8n if present)",
    )
    parser.add_argument(
        "--confidence",
        type=float,
        default=0.25,
        help="Detection confidence threshold between 0 and 1 (default: 0.25)",
    )
    parser.add_argument(
        "--device",
        type=str,
        default=None,
        help="torch device to run inference on (default: auto-detect)",
    )
    parser.add_argument(
        "--max-det",
        type=int,
        default=300,
        help="Maximum number of detections to retain per frame (default: 300)",
    )
    parser.add_argument(
        "--imgsz",
        type=int,
        default=None,
        help="Optional image size (pixels) passed to YOLO for inference",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Optional path to save an annotated video (e.g. output.mp4)",
    )
    parser.add_argument(
        "--no-display",
        dest="display",
        action="store_false",
        help="Disable realtime window display",
    )
    parser.add_argument(
        "--display",
        dest="display",
        action="store_true",
        help=argparse.SUPPRESS,
    )
    parser.set_defaults(display=True)
    parser.add_argument(
        "--no-throttle",
        dest="throttle",
        action="store_false",
        help="Process as fast as possible instead of syncing to the source FPS",
    )
    parser.add_argument(
        "--throttle",
        dest="throttle",
        action="store_true",
        help=argparse.SUPPRESS,
    )
    parser.set_defaults(throttle=True)
    parser.add_argument(
        "--max-frames",
        type=int,
        default=None,
        help="Stop after processing this many frames (default: entire video)",
    )
    return parser.parse_args(list(argv) if argv is not None else None)


def _resolve_device(preferred: Optional[str]) -> str:
    if preferred:
        return preferred
    return "cuda" if torch.cuda.is_available() else "cpu"


def _open_video(path: Path) -> cv2.VideoCapture:
    capture = cv2.VideoCapture(str(path))
    if not capture.isOpened():
        raise FileNotFoundError(f"Unable to open video: {path}")
    return capture


def _initialise_writer(cap: cv2.VideoCapture, output_path: Path) -> cv2.VideoWriter:
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    fps = cap.get(cv2.CAP_PROP_FPS)
    fps = fps if fps and fps > 0 else 30.0
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    return cv2.VideoWriter(str(output_path), fourcc, fps, (width, height))


def _resolve_label(names: Iterable[str] | dict[int, str], class_idx: int) -> str:
    if isinstance(names, dict):
        return names.get(class_idx, str(class_idx))
    if isinstance(names, list):
        if 0 <= class_idx < len(names):
            return names[class_idx]
        return str(class_idx)
    return str(class_idx)


def _draw_detections(frame, result, *, confidence: float) -> int:
    boxes = getattr(result, "boxes", None)
    if boxes is None or len(boxes) == 0:
        return 0

    detections = 0
    names = result.names
    for cls_val, conf_val, box_tensor in zip(boxes.cls.tolist(), boxes.conf.tolist(), boxes.xyxy):
        if conf_val < confidence:
            continue
        x1, y1, x2, y2 = [int(v) for v in box_tensor.tolist()]
        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
        label = _resolve_label(names, int(cls_val))
        caption = f"{label} {conf_val:.2f}"
        text_org = (x1, max(15, y1 - 10))
        cv2.putText(frame, caption, text_org, cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 3, cv2.LINE_AA)
        cv2.putText(frame, caption, text_org, cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)
        detections += 1
    return detections


def _overlay_metrics(frame, fps: float, detections: int) -> None:
    overlay = f"FPS: {fps:.1f} | detections: {detections}"
    cv2.putText(frame, overlay, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 3, cv2.LINE_AA)
    cv2.putText(frame, overlay, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 1, cv2.LINE_AA)


def _process_video(args: argparse.Namespace) -> VideoSummary:
    video_path = args.video.expanduser().resolve()
    if not video_path.exists():
        raise FileNotFoundError(f"Video file not found: {video_path}")

    device = _resolve_device(args.device)
    model = YOLO(str(args.weights))
    model.to(device)

    cap = _open_video(video_path)
    writer = _initialise_writer(cap, args.output) if args.output else None

    source_fps = cap.get(cv2.CAP_PROP_FPS)
    source_fps = source_fps if source_fps and source_fps > 0 else 0.0
    frame_interval = (1.0 / source_fps) if (args.throttle and source_fps > 0) else 0.0

    summary = VideoSummary()
    rolling_start = time.perf_counter()

    print(f"Running YOLOv8 realtime labelling on: {video_path}")
    print(f"Using weights: {args.weights} | device: {device}")
    if source_fps:
        print(f"Source FPS: {source_fps:.2f}")
    if args.output:
        print(f"Saving annotated video to: {args.output}")
    print("Press 'q' in the display window to stop early.\n")

    try:
        while True:
            if args.max_frames is not None and summary.total_frames >= args.max_frames:
                break

            ret, frame = cap.read()
            if not ret:
                break

            loop_start = time.perf_counter()
            infer_start = loop_start
            predict_kwargs = {
                "conf": args.confidence,
                "verbose": False,
                "device": device,
                "max_det": args.max_det,
                "stream": False,
            }
            if args.imgsz is not None:
                predict_kwargs["imgsz"] = args.imgsz

            results = model.predict(frame, **predict_kwargs)
            result = results[0] if results else None
            annotated = frame

            frame_detections = 0
            if result is not None:
                frame_detections = _draw_detections(annotated, result, confidence=args.confidence)

            infer_elapsed = time.perf_counter() - infer_start
            fps = 1.0 / infer_elapsed if infer_elapsed > 0 else 0.0
            _overlay_metrics(annotated, fps, frame_detections)

            if writer is not None:
                writer.write(annotated)

            if args.display:
                try:
                    cv2.imshow("YOLOv8 realtime", annotated)
                except cv2.error as exc:
                    print(f"[warning] Display unavailable ({exc}); disabling window output.")
                    args.display = False
                else:
                    if cv2.waitKey(1) & 0xFF == ord("q"):
                        print("Stopping due to user input.")
                        break

            summary.total_frames += 1
            summary.total_detections += frame_detections

            if frame_interval > 0:
                elapsed_since_start = time.perf_counter() - loop_start
                sleep_time = frame_interval - elapsed_since_start
                if sleep_time > 0:
                    time.sleep(sleep_time)

        elapsed_total = time.perf_counter() - rolling_start
        summary.avg_fps = summary.total_frames / elapsed_total if elapsed_total > 0 else 0.0

    finally:
        cap.release()
        if writer is not None:
            writer.release()
        if args.display and hasattr(cv2, "destroyAllWindows"):
            try:
                cv2.destroyAllWindows()
            except cv2.error as exc:
                print(f"[warning] destroyAllWindows unavailable ({exc}).")

    return summary


def main(argv: Sequence[str] | None = None) -> int:
    try:
        args = parse_args(argv)
        summary = _process_video(args)
    except FileNotFoundError as exc:
        print(f"[error] {exc}", file=sys.stderr)
        return 1
    except Exception as exc:  # pragma: no cover - runtime failure surface
        print(f"[error] Unexpected failure: {exc}", file=sys.stderr)
        return 2

    print(
        f"\nProcessed {summary.total_frames} frame(s) | "
        f"detections: {summary.total_detections} | average FPS: {summary.avg_fps:.2f}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
