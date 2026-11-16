"""Benchmark periodic cKDTree and a teaching Cell-linked List implementation."""
from __future__ import annotations

import argparse
import csv
import statistics
import time
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import FuncFormatter

from src.cell_list import counts_cell_list
from src.neighbors import counts_kdtree, generate_positions


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results"


def timed_call(function, positions, box, cutoff):
    start = time.perf_counter()
    result = function(positions, box, cutoff)
    return result, time.perf_counter() - start


def write_figure(rows):
    paper_style = {
        "font.family": "DejaVu Sans",
        "font.size": 7.2,
        "axes.titlesize": 8.5,
        "axes.titleweight": "regular",
        "axes.labelsize": 7.5,
        "xtick.labelsize": 6.8,
        "ytick.labelsize": 6.8,
        "axes.linewidth": 0.6,
        "legend.fontsize": 6.8,
        "legend.frameon": True,
        "legend.framealpha": 0.92,
        "legend.borderpad": 0.35,
        "legend.handlelength": 2.0,
        "legend.labelspacing": 0.3,
        "figure.facecolor": "white",
        "axes.facecolor": "white",
        "savefig.facecolor": "white",
    }
    with plt.rc_context(paper_style):
        fig, axis = plt.subplots(figsize=(5.2, 3.4))
        styles = {
            "kdtree": {
                "label": "Periodic cKDTree",
                "color": "#2878B5",
                "marker": "o",
            },
            "cell_list": {
                "label": "Python Cell List",
                "color": "#D94B3D",
                "marker": "s",
            },
        }
        for method, style in styles.items():
            selected = sorted(
                (row for row in rows if row["method"] == method),
                key=lambda row: row["n"],
            )
            sizes = np.array([row["n"] for row in selected])
            median = np.array([row["median_wall_s"] for row in selected])
            minimum = np.array([row["min_wall_s"] for row in selected])
            maximum = np.array([row["max_wall_s"] for row in selected])
            axis.plot(
                sizes,
                median,
                linewidth=1.0,
                markersize=3.5,
                markeredgewidth=0.55,
                zorder=3,
                **style,
            )
            axis.fill_between(
                sizes,
                minimum,
                maximum,
                color=style["color"],
                alpha=0.10,
                linewidth=0,
                zorder=2,
            )

        axis.set_xscale("log")
        axis.set_yscale("log")
        axis.set_xticks([1000, 5000, 10000])
        axis.xaxis.set_major_formatter(
            FuncFormatter(lambda value, _: f"{value / 1000:g}k")
        )
        axis.set_xlabel("Number of particles, N", labelpad=3)
        axis.set_ylabel("Wall time per call (s)", labelpad=3)
        axis.set_title("Periodic neighbor-search runtime", pad=5)
        axis.grid(
            True,
            which="major",
            color="#D7D7D7",
            linestyle="--",
            linewidth=0.4,
            alpha=0.45,
        )
        axis.grid(
            True,
            which="minor",
            color="#E8E8E8",
            linestyle=":",
            linewidth=0.3,
            alpha=0.45,
        )
        for spine in axis.spines.values():
            spine.set_color("#4D4D4D")
            spine.set_linewidth(0.6)
        legend = axis.legend(loc="upper left")
        legend.get_frame().set_edgecolor("#D2D2D2")
        legend.get_frame().set_linewidth(0.55)
        axis.text(
            0.98,
            0.035,
            "shading: min–max  ·  counts identical",
            transform=axis.transAxes,
            ha="right",
            va="bottom",
            fontsize=6.7,
            color="#666666",
        )
        axis.tick_params(which="major", length=3.2, width=0.65, color="#4D4D4D")
        axis.tick_params(which="minor", length=2.0, width=0.45, color="#777777")
        fig.tight_layout(pad=0.8)
    fig.savefig(OUT / "fig06_cell_list_benchmark.png", dpi=300)
    fig.savefig(OUT / "fig06_cell_list_benchmark.pdf", bbox_inches="tight")
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--sizes", type=int, nargs="+", default=[1000, 5000, 10000])
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--seed", type=int, default=20261116)
    parser.add_argument("--cutoff", type=float, default=3.0)
    args = parser.parse_args()
    if args.repeats < 1 or any(size < 1 for size in args.sizes):
        parser.error("sizes and repeats must be positive")

    OUT.mkdir(exist_ok=True)
    rows = []
    methods = [("kdtree", counts_kdtree), ("cell_list", counts_cell_list)]
    for n in args.sizes:
        positions, box = generate_positions(n, seed=args.seed)
        reference = None
        for method, function in methods:
            elapsed = []
            first_result = None
            for _ in range(args.repeats):
                result, wall_time = timed_call(function, positions, box, args.cutoff)
                if first_result is None:
                    first_result = result
                else:
                    np.testing.assert_array_equal(result, first_result)
                elapsed.append(wall_time)
            if reference is None:
                reference = first_result
            else:
                np.testing.assert_array_equal(first_result, reference)
            row = {
                "n": n,
                "method": method,
                "median_wall_s": statistics.median(elapsed),
                "min_wall_s": min(elapsed),
                "max_wall_s": max(elapsed),
                "mean_coordination": float(first_result.mean()),
                "sum_coordination": int(first_result.sum()),
                "repeats": args.repeats,
                "seed": args.seed,
                "cutoff_A": args.cutoff,
            }
            rows.append(row)
            print(
                f"N={n:>6} {method:<9} median={row['median_wall_s']:.6f}s "
                f"mean_CN={row['mean_coordination']:.3f}",
                flush=True,
            )

    fieldnames = list(rows[0])
    with (OUT / "benchmark_cell_list.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    write_figure(rows)
    print("Wrote benchmark_cell_list.csv and fig06_cell_list_benchmark.png/.pdf")


if __name__ == "__main__":
    main()
