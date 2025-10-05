from __future__ import annotations

import argparse
import csv
import itertools
import statistics
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

from .evaluate_dataset import EvaluationRecord, evaluate_dataset


def _coerce_override(value: float | int | str) -> str:
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value)


def _summarize(records: Sequence[EvaluationRecord]) -> Dict[str, float]:
    total = len(records)
    detections = sum(1 for record in records if record.detected)
    avg_conf = statistics.fmean(record.confidence_pct for record in records) if records else 0.0
    snrs = [record.snr_db for record in records if record.snr_db is not None]
    avg_snr = statistics.fmean(snrs) if snrs else 0.0
    fundamentals = [record.fundamental_hz for record in records if record.fundamental_hz is not None]
    avg_fund = statistics.fmean(fundamentals) if fundamentals else 0.0

    return {
        "total_files": float(total),
        "detections": float(detections),
        "detection_rate": (detections / total) if total else 0.0,
        "avg_confidence": avg_conf,
        "avg_snr": avg_snr,
        "avg_fundamental": avg_fund,
    }


def _ensure_path(path: Path) -> Path:
    resolved = path.expanduser().resolve()
    if not resolved.exists():
        raise FileNotFoundError(f"Dataset root '{resolved}' does not exist")
    return resolved


def _parse_overrides(raw: Iterable[str]) -> Dict[str, str]:
    overrides: Dict[str, str] = {}
    for item in raw:
        key, sep, value = item.partition("=")
        if not sep:
            raise ValueError(f"Overrides must be KEY=VALUE, got '{item}'")
        overrides[key.strip()] = value.strip()
    return overrides


def _build_grid(args: argparse.Namespace) -> Tuple[List[str], List[Tuple[float, ...]]]:
    values: Dict[str, Sequence[float]] = {
        "prominence_ratio": args.prominence_ratio,
        "min_bpf_hz": args.min_bpf,
        "max_bpf_hz": args.max_bpf,
        "num_harmonics": args.harmonics,
        "noise_floor_db": args.noise_floor,
    }
    names = [name for name, vals in values.items() if vals]
    if not names:
        return [], [tuple()]

    combos = list(itertools.product(*(values[name] for name in names)))
    return names, combos


def _row_for(
    names: Sequence[str],
    combo: Tuple[float, ...],
    positive_summary: Dict[str, float],
    negative_summary: Optional[Dict[str, float]],
) -> Dict[str, float | str | None]:
    row: Dict[str, float | str | None] = {}
    for name, value in zip(names, combo):
        row[name] = value

    row.update(
        {
            "positive_total_files": positive_summary["total_files"],
            "positive_detections": positive_summary["detections"],
            "positive_detection_rate": positive_summary["detection_rate"],
            "positive_avg_confidence": positive_summary["avg_confidence"],
            "positive_avg_snr": positive_summary["avg_snr"],
            "positive_avg_fundamental": positive_summary["avg_fundamental"],
        }
    )

    if negative_summary is not None:
        row.update(
            {
                "negative_total_files": negative_summary["total_files"],
                "negative_detections": negative_summary["detections"],
                "negative_detection_rate": negative_summary["detection_rate"],
                "negative_avg_confidence": negative_summary["avg_confidence"],
                "negative_avg_snr": negative_summary["avg_snr"],
                "negative_avg_fundamental": negative_summary["avg_fundamental"],
            }
        )
    return row


def run_sweep(args: argparse.Namespace) -> List[Dict[str, float | str | None]]:
    positive_root = _ensure_path(args.positive_root)
    negative_root = None
    if args.negative_root is not None:
        try:
            negative_root = _ensure_path(args.negative_root)
        except FileNotFoundError:
            print(f"[warn] Negative dataset root '{args.negative_root}' not found; skipping negative sweep")
            negative_root = None

    names, combos = _build_grid(args)
    if not combos:
        combos = [tuple()]

    constant_overrides = _parse_overrides(args.override)

    results: List[Dict[str, float | str | None]] = []
    for index, combo in enumerate(combos, start=1):
        overrides: Dict[str, str] = dict(constant_overrides)
        overrides.update({name: _coerce_override(value) for name, value in zip(names, combo)})

        label = ", ".join(f"{key}={value}" for key, value in overrides.items()) or "(defaults)"
        print(f"[{index}/{len(combos)}] Evaluating parameters: {label}")

        positive_records = evaluate_dataset(
            positive_root,
            max_files=args.max_positive,
            overrides=overrides,
            save_reports=False,
            show_progress=not args.quiet,
            shuffle_seed=args.seed,
        )
        positive_summary = _summarize(positive_records)

        negative_summary: Optional[Dict[str, float]] = None
        if negative_root is not None:
            negative_records = evaluate_dataset(
                negative_root,
                max_files=args.max_negative,
                overrides=overrides,
                save_reports=False,
                show_progress=False,
                shuffle_seed=args.seed,
            )
            negative_summary = _summarize(negative_records)

        row = _row_for(names, combo, positive_summary, negative_summary)
        row["overrides"] = label
        results.append(row)

        print(
            f"    Positive detection rate: {positive_summary['detection_rate']*100:.2f}% "
            f"over {positive_summary['total_files']:.0f} files"
        )
        if negative_summary is not None:
            print(
                f"    Negative detection rate: {negative_summary['detection_rate']*100:.2f}% "
                f"over {negative_summary['total_files']:.0f} files"
            )

    return results


def _write_results(path: Path, rows: List[Dict[str, float | str | None]]) -> None:
    if not rows:
        print("[warn] No results to write")
        return

    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = sorted({key for row in rows for key in row.keys()})
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"[info] Results written to {path}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Sweep acoustic detector parameters across datasets")
    parser.add_argument(
        "--positive-root",
        type=Path,
        default=Path("MLSP_2022_Real_Data/real_data"),
        help="Path to positive (drone) dataset root",
    )
    parser.add_argument(
        "--negative-root",
        type=Path,
        default=Path("ESC-50/audio"),
        help="Path to negative (no-drone) dataset root",
    )
    parser.add_argument("--max-positive", type=int, default=2000, help="Max files to sample from the positive dataset")
    parser.add_argument("--max-negative", type=int, default=2000, help="Max files to sample from the negative dataset")
    parser.add_argument("--seed", type=int, default=123, help="Shuffle seed for deterministic sampling")
    parser.add_argument("--quiet", action="store_true", help="Suppress progress bars during evaluation")
    parser.add_argument(
        "--prominence-ratio",
        type=float,
        nargs="*",
        default=[6.0, 8.0, 10.0, 12.0],
        help="Prominence ratios to evaluate",
    )
    parser.add_argument(
        "--min-bpf",
        type=float,
        nargs="*",
        default=[30.0, 40.0, 60.0],
        help="Minimum BPF frequencies (Hz) to sweep",
    )
    parser.add_argument(
        "--max-bpf",
        type=float,
        nargs="*",
        default=[2000.0, 2500.0],
        help="Maximum BPF frequencies (Hz) to sweep",
    )
    parser.add_argument(
        "--harmonics",
        type=int,
        nargs="*",
        default=[4, 6, 8],
        help="Number of harmonics to request",
    )
    parser.add_argument(
        "--noise-floor",
        type=float,
        nargs="*",
        default=[-42.0, -38.0],
        help="Noise floor estimates (dB) to sweep",
    )
    parser.add_argument(
        "--override",
        action="append",
        default=[],
        metavar="KEY=VALUE",
        help="Additional overrides applied to every sweep entry",
    )
    parser.add_argument("--output", type=Path, default=Path("reports/parameter_sweep.csv"), help="Output CSV path")
    return parser


def main(argv: Optional[Sequence[str]] = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        rows = run_sweep(args)
    except FileNotFoundError as exc:
        parser.error(str(exc))
        return

    if args.output:
        _write_results(args.output, rows)

    rows_sorted = sorted(rows, key=lambda row: row.get("positive_detection_rate", 0), reverse=True)
    print("\nTop configurations by positive detection rate:")
    for row in rows_sorted[:10]:
        pos_rate = row.get("positive_detection_rate", 0) or 0
        neg_rate = row.get("negative_detection_rate", 0)
        print(
            f"  - {row['overrides']}: +{pos_rate*100:.2f}%"
            + (f", -{(neg_rate or 0)*100:.2f}%" if neg_rate is not None else "")
        )


if __name__ == "__main__":  # pragma: no cover
    main()
