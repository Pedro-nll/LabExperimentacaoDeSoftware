#!/usr/bin/env python3
"""Combine the 4 quality-metric scatter plots of each RQ into one image."""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt

RQ_PREFIXES = [
    "rq1_popularity",
    "rq2_maturity",
    "rq3_activity",
    "rq4_size",
]

METRIC_ORDER = [
    "cbo_median",
    "dit_median",
    "lcom_median",
    "lcom_star_median",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Combine 4 RQ scatter plots into one image per RQ")
    parser.add_argument(
        "--input-dir",
        default="enunciado2/output/rq_graphs",
        help="Directory containing individual scatter PNG files",
    )
    parser.add_argument(
        "--output-dir",
        default="enunciado2/output/rq_graphs",
        help="Directory where combined PNG files will be saved",
    )
    return parser.parse_args()


def combine_one_rq(input_dir: Path, output_dir: Path, rq_prefix: str) -> bool:
    images = []
    labels = []
    for metric in METRIC_ORDER:
        path = input_dir / f"{rq_prefix}_{metric}.png"
        if not path.exists():
            print(f"Skipping {rq_prefix}: missing file {path.name}")
            return False
        images.append(plt.imread(path))
        labels.append(metric.replace("_median", "").upper().replace("_", "*"))

    fig, axes = plt.subplots(2, 2, figsize=(20, 14))
    fig.suptitle(f"{rq_prefix} - Combined Scatter Plots", fontsize=16)

    for idx, ax in enumerate(axes.flat):
        ax.imshow(images[idx])
        ax.set_title(labels[idx], fontsize=12)
        ax.axis("off")

    fig.tight_layout(rect=[0, 0, 1, 0.97])
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{rq_prefix}_combined.png"
    fig.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close(fig)

    print(f"Created {output_path}")
    return True


def main() -> int:
    args = parse_args()
    input_dir = Path(args.input_dir).resolve()
    output_dir = Path(args.output_dir).resolve()

    if not input_dir.exists():
        raise FileNotFoundError(f"Input directory not found: {input_dir}")

    created = 0
    for rq_prefix in RQ_PREFIXES:
        if combine_one_rq(input_dir=input_dir, output_dir=output_dir, rq_prefix=rq_prefix):
            created += 1

    print(f"Combined panels created: {created}/{len(RQ_PREFIXES)}")
    return 0 if created else 1


if __name__ == "__main__":
    raise SystemExit(main())
