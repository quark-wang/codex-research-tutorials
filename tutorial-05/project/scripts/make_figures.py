"""Render five publication-style figures from benchmark data and tested code."""
from __future__ import annotations

import csv
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from src.neighbors import counts_kdtree, generate_positions

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results"

COLORS = {"dense": "#e31a1c", "kdtree": "#1f78b4"}


def _style():
    plt.rcParams.update(
        {
            "figure.dpi": 140,
            "savefig.dpi": 300,
            "font.family": "DejaVu Sans",
            "font.size": 8.0,
            "axes.titlesize": 9.0,
            "axes.titleweight": "normal",
            "axes.labelsize": 8.0,
            "axes.linewidth": 0.8,
            "axes.spines.top": True,
            "axes.spines.right": True,
            "axes.grid": True,
            "grid.alpha": 0.32,
            "grid.color": "#c7c7c7",
            "grid.linestyle": ":",
            "grid.linewidth": 0.55,
            "xtick.labelsize": 7.2,
            "ytick.labelsize": 7.2,
            "xtick.major.width": 0.75,
            "ytick.major.width": 0.75,
            "xtick.major.size": 3.0,
            "ytick.major.size": 3.0,
            "legend.fontsize": 7.0,
            "legend.frameon": True,
            "legend.framealpha": 0.88,
            "legend.facecolor": "white",
            "legend.edgecolor": "#bdbdbd",
            "legend.borderpad": 0.3,
            "legend.handlelength": 1.7,
            "legend.labelspacing": 0.25,
            "figure.facecolor": "white",
            "axes.facecolor": "white",
        }
    )


def _save(fig, name):
    fig.tight_layout(pad=0.65)
    fig.savefig(OUT / f"{name}.png", bbox_inches="tight", facecolor="white")
    fig.savefig(OUT / f"{name}.pdf", bbox_inches="tight", facecolor="white")
    plt.close(fig)


def _load_rows():
    path = OUT / "benchmark.csv"
    if not path.is_file():
        raise FileNotFoundError("run `python -m scripts.benchmark --repeats 3` first")
    with path.open(newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))


def main():
    OUT.mkdir(exist_ok=True)
    _style()
    rows = _load_rows()
    groups = {
        method: sorted(
            (row for row in rows if row["method"] == method),
            key=lambda row: int(row["n"]),
        )
        for method in ("dense", "kdtree")
    }

    fig, ax = plt.subplots(figsize=(5.2, 3.25))
    labels = {"dense": "Dense N×N (≤2k)", "kdtree": "Periodic cKDTree"}
    markers = {"dense": "s", "kdtree": "o"}
    for method, group in groups.items():
        x = np.array([int(row["n"]) for row in group])
        y = np.array([float(row["median_wall_s"]) for row in group])
        lower = y - np.array([float(row["min_wall_s"]) for row in group])
        upper = np.array([float(row["max_wall_s"]) for row in group]) - y
        ax.errorbar(
            x,
            y,
            yerr=np.vstack([lower, upper]),
            marker=markers[method],
            capsize=2,
            capthick=0.8,
            elinewidth=0.8,
            linewidth=1.1,
            markersize=3.8,
            color=COLORS[method],
            label=labels[method],
        )
    ax.set(xlabel="Atom count, N", ylabel="Wall time per call (s)")
    ax.set_title("Neighbor-search runtime (3 independent processes)", pad=4)
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.legend(loc="upper left")
    _save(fig, "fig01_runtime")

    fig, ax = plt.subplots(figsize=(5.2, 3.25))
    for method, group in groups.items():
        x = np.array([int(row["n"]) for row in group])
        y = np.array([float(row["median_peak_rss_mib"]) for row in group])
        ax.plot(
            x,
            y,
            marker=markers[method],
            linewidth=1.1,
            markersize=3.8,
            color=COLORS[method],
            label=labels[method],
        )
    ax.set(xlabel="Atom count, N", ylabel="Peak working set (MiB)")
    ax.set_title("Peak process memory", pad=4)
    ax.set_xscale("log")
    ax.legend(loc="upper left")
    ax.text(
        0.98,
        0.05,
        "Dense at 30k: not run\nΔ array alone ≈ 20.1 GiB",
        transform=ax.transAxes,
        ha="right",
        va="bottom",
        fontsize=6.7,
        color="#444444",
        bbox={"boxstyle": "round,pad=0.25", "facecolor": "white", "edgecolor": "#cccccc", "alpha": 0.9},
    )
    _save(fig, "fig02_peak_rss")

    fig, ax = plt.subplots(figsize=(5.0, 3.35))
    coords = np.array([[0.2, 5, 5], [9.8, 5, 5], [5, 5, 5], [5.5, 5, 5]])
    ax.grid(False)
    ax.plot([0, 10, 10, 0, 0], [0, 0, 10, 10, 0], color="#222222", linewidth=0.9)
    ax.scatter(coords[:, 0], coords[:, 1], s=27, color="#111111", zorder=4)
    ax.plot([9.8, 10.0], [5, 5], color="#e31a1c", linewidth=1.4, linestyle="--")
    ax.plot([0.0, 0.2], [5, 5], color="#e31a1c", linewidth=1.4, linestyle="--")
    ax.annotate(
        "0.4 Å via PBC",
        xy=(0.2, 5),
        xytext=(1.15, 2.4),
        color="#e31a1c",
        fontsize=7.2,
        arrowprops={"arrowstyle": "->", "color": "#e31a1c", "lw": 0.8},
    )
    ax.annotate(
        "9.6 Å direct separation",
        xy=(9.8, 5),
        xytext=(6.9, 7.5),
        ha="center",
        fontsize=7.2,
        color="#444444",
        arrowprops={"arrowstyle": "->", "color": "#777777", "lw": 0.75},
    )
    ax.text(5.25, 5.35, "interior pair", ha="center", fontsize=6.5, color="#555555")
    ax.set(
        xlim=(-0.55, 10.55),
        ylim=(-0.45, 10.45),
        xlabel="x (Å)",
        ylabel="y (Å)",
        title="Minimum-image geometry in a periodic box",
    )
    ax.set_aspect("equal")
    _save(fig, "fig03_periodic_boundary")

    xyz, box = generate_positions(10000, seed=20261116)
    counts = counts_kdtree(xyz, box, 3.0)
    values, frequency = np.unique(counts, return_counts=True)
    fig, ax = plt.subplots(figsize=(5.2, 3.25))
    ax.bar(
        values,
        frequency,
        width=0.82,
        color="#4c78a8",
        edgecolor="white",
        linewidth=0.35,
        alpha=0.92,
    )
    ax.axvline(
        counts.mean(),
        color="#e31a1c",
        linestyle="--",
        linewidth=1.0,
        label=f"mean = {counts.mean():.3f}",
    )
    ax.set(xlabel="Coordination number (r ≤ 3 Å)", ylabel="Atom count")
    ax.set_title("Coordination-number distribution (N = 10,000)", pad=4)
    ax.legend(loc="upper right")
    _save(fig, "fig04_coordination_hist")

    sizes = np.array([500, 1000, 2000, 5000, 10000, 30000], dtype=float)
    theoretical_delta_gib = 3 * sizes**2 * 8 / 1024**3
    fig, ax = plt.subplots(figsize=(5.2, 3.25))
    ax.plot(
        sizes,
        theoretical_delta_gib,
        marker="o",
        markersize=3.8,
        color="#6a3d9a",
        linewidth=1.1,
    )
    ax.set(xlabel="Atom count, N", ylabel="Δ array alone (GiB)")
    ax.set_title("Dense displacement-array memory", pad=4)
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.annotate(
        f"30k: {theoretical_delta_gib[-1]:.1f} GiB",
        xy=(sizes[-1], theoretical_delta_gib[-1]),
        xytext=(-48, -13),
        textcoords="offset points",
        fontsize=6.8,
        color="#6a3d9a",
        arrowprops={"arrowstyle": "->", "color": "#6a3d9a", "lw": 0.7},
    )
    ax.text(
        0.03,
        0.95,
        "Analytical estimate, not a measurement",
        transform=ax.transAxes,
        va="top",
        fontsize=6.7,
        color="#555555",
    )
    _save(fig, "fig05_theoretical_memory")

    print("Generated 5 PNG and 5 PDF files in results/")


if __name__ == "__main__":
    main()

