from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from statistics import mean
from typing import Dict, Iterable, List, Optional

try:  # pragma: no cover - optional dependency
    import matplotlib.pyplot as plt
except ImportError:  # pragma: no cover - handled in runtime
    plt = None


@dataclass
class Record:
    relative_path: str
    label: str
    configuration: Optional[str]
    mission: Optional[str]
    detected: bool
    fundamental_hz: Optional[float]
    harmonics: int
    confidence_pct: int
    snr_db: Optional[float]
    peak_db: Optional[float]
    noise_floor_db: Optional[float]
    description: str


def _coerce_optional_float(value: str) -> Optional[float]:
    value = value.strip()
    if not value:
        return None
    try:
        return float(value)
    except ValueError:
        return None


def load_records(path: Path) -> List[Record]:
    if not path.exists():
        raise FileNotFoundError(f"Report file '{path}' not found. Run evaluate_dataset first.")

    records: List[Record] = []
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            records.append(
                Record(
                    relative_path=row["relative_path"],
                    label=row["label"],
                    configuration=row.get("configuration") or None,
                    mission=row.get("mission") or None,
                    detected=row["detected"].strip().lower() in {"1", "true", "yes"},
                    fundamental_hz=_coerce_optional_float(row.get("fundamental_hz", "")),
                    harmonics=int(row.get("harmonics", 0) or 0),
                    confidence_pct=int(row.get("confidence_pct", 0) or 0),
                    snr_db=_coerce_optional_float(row.get("snr_db", "")),
                    peak_db=_coerce_optional_float(row.get("peak_db", "")),
                    noise_floor_db=_coerce_optional_float(row.get("noise_floor_db", "")),
                    description=row.get("description", ""),
                )
            )
    if not records:
        raise ValueError(f"No rows found in '{path}'.")
    return records


def aggregate(records: Iterable[Record]) -> Dict[str, Dict[str, float]]:
    aggregates: Dict[str, Dict[str, float]] = defaultdict(lambda: {
        "count": 0,
        "detections": 0,
        "confidences": [],
        "fundamentals": [],
    })
    for record in records:
        bucket = aggregates[record.label]
        bucket["count"] += 1
        bucket["detections"] += int(record.detected)
        bucket["confidences"].append(record.confidence_pct)
        if record.detected and record.fundamental_hz is not None:
            bucket["fundamentals"].append(record.fundamental_hz)
    return aggregates


def _require_matplotlib() -> None:
    if plt is None:
        raise RuntimeError(
            "matplotlib is required for visualization. Install it via 'uv add matplotlib'."
        )


def render_figures(
    aggregates: Dict[str, Dict[str, float]],
    records: List[Record],
    output: Path,
    *,
    show: bool,
) -> None:
    _require_matplotlib()
    labels = sorted(aggregates.keys())
    detection_rates = []
    avg_confidences = []
    avg_fundamental = []

    for label in labels:
        data = aggregates[label]
        count = data["count"] or 1
        detection_rates.append(100.0 * data["detections"] / count)
        avg_confidences.append(mean(data["confidences"]) if data["confidences"] else 0.0)
        avg_fundamental.append(mean(data["fundamentals"]) if data["fundamentals"] else 0.0)

    detected_records = [r for r in records if r.detected and r.fundamental_hz is not None]
    fundamentals = [r.fundamental_hz for r in detected_records]
    confidences = [r.confidence_pct for r in detected_records]

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    axes[0].bar(labels, detection_rates, color="#4C72B0", alpha=0.85, label="Detection rate (%)")
    axes[0].plot(labels, avg_confidences, color="#55A868", marker="o", label="Avg confidence (%)")
    axes[0].set_ylim(0, 105)
    axes[0].set_ylabel("Percentage")
    axes[0].set_title("Detection rate and confidence per label")
    axes[0].grid(axis="y", linestyle="--", alpha=0.5)
    axes[0].legend()

    axes[1].scatter(
        fundamentals,
        confidences,
        c="tab:orange",
        alpha=0.7,
        edgecolors="k",
        linewidths=0.5,
    )
    axes[1].set_xlabel("Fundamental frequency (Hz)")
    axes[1].set_ylabel("Confidence (%)")
    axes[1].set_title("Detected fundamentals vs confidence")
    axes[1].grid(True, linestyle="--", alpha=0.5)

    fig.suptitle("UAV Propeller Acoustic Evaluation", fontsize=16)
    fig.tight_layout(rect=[0, 0, 1, 0.96])

    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, dpi=150)
    if show:
        plt.show()
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Visualise evaluation results produced by evaluate_dataset."
    )
    parser.add_argument(
        "input",
        type=Path,
        nargs="?",
        default=Path("reports/propeller_eval.csv"),
        help="Path to the CSV report file (default: reports/propeller_eval.csv)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("reports/propeller_eval_summary.png"),
        help="Output path for the generated PNG chart",
    )
    parser.add_argument(
        "--show",
        action="store_true",
        help="Display the figure window in addition to saving the PNG",
    )
    args = parser.parse_args()

    records = load_records(args.input)
    aggregates = aggregate(records)
    render_figures(aggregates, records, args.output, show=args.show)

    print("Visualisation saved to", args.output)
    for label, stats in aggregates.items():
        rate = 100.0 * stats["detections"] / stats["count"] if stats["count"] else 0.0
        avg_conf = mean(stats["confidences"]) if stats["confidences"] else 0.0
        print(f"  - {label}: {rate:.1f}% detection rate, avg confidence {avg_conf:.1f}%")


if __name__ == "__main__":  # pragma: no cover
    main()
