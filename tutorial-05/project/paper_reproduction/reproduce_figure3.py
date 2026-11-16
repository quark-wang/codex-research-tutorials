"""Reproduce the workload behind freud (2020), Figure 3.

This script benchmarks complete tree construction plus a periodic radius query on
the same deterministic point sets. SciPy returns directed neighbor lists including
self; freud is configured with ``exclude_ii=False`` to use the same definition.

The generated measurements are new results from the current machine. They are not
digitized values from the published figure, and absolute timings are not expected
to match the paper's Intel Xeon E5-2680 v2 system.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import os
import platform
import statistics
import sys
import time
from pathlib import Path
from typing import Any, Callable

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import scipy
from scipy.spatial import cKDTree


# Exact point counts used by the published Figure 3 benchmark notebook.
DEFAULT_SIZES = (50, 80, 100, 200, 400, 600, 1000, 2000, 3000, 5000)
DEFAULT_SEED = 20261116
R_MAX = 1.0
TARGET_NEIGHBORS_EXCLUDING_SELF = 12.0


def box_length(n: int, target_neighbors: float = TARGET_NEIGHBORS_EXCLUDING_SELF,
               radius: float = R_MAX) -> float:
    """Return the cube length giving the requested expected neighbor count."""
    if not isinstance(n, (int, np.integer)) or int(n) <= 0:
        raise ValueError("n must be a positive integer")
    if not np.isfinite(target_neighbors) or target_neighbors <= 0:
        raise ValueError("target_neighbors must be positive and finite")
    if not np.isfinite(radius) or radius <= 0:
        raise ValueError("radius must be positive and finite")
    sphere_volume = 4.0 * math.pi * radius**3 / 3.0
    return float((int(n) * sphere_volume / target_neighbors) ** (1.0 / 3.0))


def generate_points(n: int, seed: int = DEFAULT_SEED) -> tuple[float, np.ndarray]:
    """Generate deterministic uniform points in ``[-L/2, L/2)``."""
    length = box_length(n)
    # Make every size deterministic while avoiding identical prefixes across sizes.
    rng = np.random.default_rng(int(seed) + 1_000_003 * int(n))
    points = (rng.random((int(n), 3)) - 0.5) * length
    return length, np.ascontiguousarray(points, dtype=np.float32)


def scipy_query(length: float, points: np.ndarray) -> int:
    """Build a periodic cKDTree and materialize directed neighbors incl. self."""
    shifted = (np.asarray(points, dtype=np.float64) + length / 2.0) % length
    tree = cKDTree(shifted, boxsize=length)
    result = tree.query_ball_tree(tree, r=R_MAX)
    return int(sum(map(len, result)))


def freud_query(length: float, points: np.ndarray, freud_module: Any) -> int:
    """Build freud AABBQuery and materialize directed neighbors incl. self."""
    box = freud_module.box.Box.cube(float(length))
    query = freud_module.locality.AABBQuery(box, np.asarray(points, dtype=np.float32))
    neighbors = query.query(
        np.asarray(points, dtype=np.float32),
        {"r_max": R_MAX, "exclude_ii": False},
    ).toNeighborList()
    return int(len(neighbors))


def _time_complete_calls(function: Callable[[], int], number: int,
                         repeats: int) -> tuple[list[float], int]:
    """Return seconds per complete call for each repeat and the pair count."""
    if number < 1 or repeats < 1:
        raise ValueError("number and repeats must be positive")
    expected_count: int | None = None
    samples: list[float] = []
    # Warm-up is excluded from timing but validates that the method can run.
    warmup_count = int(function())
    for _ in range(repeats):
        start = time.perf_counter()
        current_count = warmup_count
        for _ in range(number):
            current_count = int(function())
        samples.append((time.perf_counter() - start) / number)
        if expected_count is None:
            expected_count = current_count
        elif current_count != expected_count:
            raise RuntimeError("neighbor count changed between identical calls")
    assert expected_count is not None
    return samples, expected_count


def _try_import_freud() -> tuple[Any | None, str | None]:
    try:
        import freud  # type: ignore
    except Exception as exc:  # import can fail because of missing native libraries
        return None, f"{type(exc).__name__}: {exc}"
    return freud, None


def _method_row(n: int, length: float, method: str, library_version: str,
                samples: list[float], count: int, number: int,
                repeats: int) -> dict[str, Any]:
    mean = statistics.fmean(samples)
    std = statistics.stdev(samples) if len(samples) > 1 else 0.0
    return {
        "n": int(n),
        "method": method,
        "library_version": library_version,
        "mean_wall_s": mean,
        "std_wall_s": std,
        "min_wall_s": min(samples),
        "max_wall_s": max(samples),
        "directed_pairs_including_self": int(count),
        "mean_neighbors_including_self": float(count / n),
        "box_length": float(length),
        "radius": R_MAX,
        "number": int(number),
        "repeats": int(repeats),
    }


def _plot(rows: list[dict[str, Any]], output_dir: Path, complete: bool) -> tuple[Path, Path]:
    """Draw a compact journal-style scaling figure from benchmark rows."""
    colors = {"scipy_cKDTree": "#2878B5", "freud_AABBQuery": "#E8752E"}
    markers = {"scipy_cKDTree": "o", "freud_AABBQuery": "s"}
    labels = {"scipy_cKDTree": "SciPy cKDTree", "freud_AABBQuery": "freud AABBQuery"}
    with plt.rc_context(
        {
            "font.family": "sans-serif",
            "font.size": 7.5,
            "axes.titlesize": 8.5,
            "axes.labelsize": 8.0,
            "axes.linewidth": 0.6,
            "xtick.labelsize": 7.0,
            "ytick.labelsize": 7.0,
            "xtick.major.width": 0.7,
            "ytick.major.width": 0.7,
            "xtick.minor.width": 0.5,
            "ytick.minor.width": 0.5,
            "legend.fontsize": 7.0,
            "figure.facecolor": "white",
            "axes.facecolor": "white",
        }
    ):
        fig, ax = plt.subplots(figsize=(5.2, 3.4))
        for method in ("scipy_cKDTree", "freud_AABBQuery"):
            group = sorted((row for row in rows if row["method"] == method),
                           key=lambda row: int(row["n"]))
            if not group:
                continue
            x = [int(row["n"]) for row in group]
            y = [float(row["mean_wall_s"]) for row in group]
            error = [float(row["std_wall_s"]) for row in group]
            version = str(group[0].get("library_version", "unknown"))
            label = f"{labels[method]} v{version}"
            ax.errorbar(
                x,
                y,
                yerr=error,
                marker=markers[method],
                markersize=3.4,
                markeredgewidth=0.55,
                capsize=1.8,
                capthick=0.65,
                elinewidth=0.65,
                linewidth=1.0,
                color=colors[method],
                label=label,
                zorder=3,
            )
        ax.set_xscale("log")
        ax.set_yscale("log")
        ax.set_xlabel("Number of points, N", labelpad=2)
        ax.set_ylabel("Build + query time (s)", labelpad=2)
        status = "SciPy + freud" if complete else "SciPy only — freud not run"
        ax.set_title(f"Neighbor-search scaling · {status}", pad=5)
        ax.grid(True, which="major", color="#BFC5CC", linewidth=0.4,
                linestyle="--", alpha=0.45)
        ax.grid(True, which="minor", color="#D8DDE2", linewidth=0.3,
                linestyle=":", alpha=0.35)
        legend = ax.legend(loc="upper left", frameon=True, handlelength=2.0,
                           borderaxespad=0.35, labelspacing=0.3, borderpad=0.3)
        legend.get_frame().set_facecolor("white")
        legend.get_frame().set_edgecolor("#C7CCD1")
        legend.get_frame().set_linewidth(0.45)
        legend.get_frame().set_alpha(0.88)
        ax.text(
            0.985,
            0.025,
            "new measurements · 100 calls × 5 repeats",
            transform=ax.transAxes,
            ha="right",
            va="bottom",
            fontsize=6.3,
            color="#666666",
        )
        ax.margins(x=0.04, y=0.10)
        fig.tight_layout(pad=0.7)
    stem = "figure3_new_benchmark" if complete else "figure3_partial_scipy_only"
    png = output_dir / f"{stem}.png"
    pdf = output_dir / f"{stem}.pdf"
    fig.savefig(png, dpi=300, bbox_inches="tight")
    fig.savefig(pdf, bbox_inches="tight")
    plt.close(fig)
    return png, pdf


def run_benchmark(output_dir: Path, sizes: list[int] | tuple[int, ...] = DEFAULT_SIZES,
                  number: int = 100, repeats: int = 5,
                  seed: int = DEFAULT_SEED, threads: int | None = None,
                  allow_partial: bool = False, freud_module: Any | None = None,
                  freud_import_error: str | None = None) -> dict[str, Any]:
    """Run the benchmark and write CSV, JSON, PNG, and PDF outputs."""
    if number < 1 or repeats < 1:
        raise ValueError("number and repeats must be positive")
    clean_sizes = [int(size) for size in sizes]
    if not clean_sizes or any(size <= 0 for size in clean_sizes):
        raise ValueError("sizes must contain positive integers")
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    if freud_module is None and not allow_partial:
        detail = f" ({freud_import_error})" if freud_import_error else ""
        raise RuntimeError(
            "freud-analysis is unavailable; install it or pass --allow-partial"
            + detail
        )
    if freud_module is not None and threads is not None:
        if threads < 1:
            raise ValueError("threads must be positive")
        freud_module.parallel.set_num_threads(int(threads))

    rows: list[dict[str, Any]] = []
    for n in clean_sizes:
        length, points = generate_points(n, seed=seed)
        scipy_samples, scipy_count = _time_complete_calls(
            lambda: scipy_query(length, points), number, repeats
        )
        rows.append(_method_row(n, length, "scipy_cKDTree", scipy.__version__,
                                scipy_samples, scipy_count, number, repeats))

        if freud_module is not None:
            freud_samples, freud_count = _time_complete_calls(
                lambda: freud_query(length, points, freud_module), number, repeats
            )
            if freud_count != scipy_count:
                raise RuntimeError(
                    f"neighbor definitions disagree for N={n}: "
                    f"SciPy={scipy_count}, freud={freud_count}"
                )
            rows.append(_method_row(
                n,
                length,
                "freud_AABBQuery",
                str(getattr(freud_module, "__version__", "unknown")),
                freud_samples,
                freud_count,
                number,
                repeats,
            ))
        print(
            f"N={n:>5} SciPy={scipy_samples and statistics.fmean(scipy_samples):.6g}s"
            + (" freud=complete" if freud_module is not None else " freud=NOT RUN"),
            flush=True,
        )

    columns = list(rows[0].keys())
    csv_path = output_dir / "new_benchmark.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)

    complete = freud_module is not None
    actual_threads: int | str | None = threads
    if freud_module is not None and hasattr(freud_module.parallel, "get_num_threads"):
        try:
            actual_threads = int(freud_module.parallel.get_num_threads())
        except Exception:
            actual_threads = threads if threads is not None else "library default"
    elif freud_module is not None and threads is None:
        actual_threads = "library default"

    metadata = {
        "status": "complete" if complete else "partial_scipy_only",
        "paper": "Ramasubramani et al., CPC 254, 107275 (2020), Figure 3 workload",
        "definition": "directed periodic neighbors including self",
        "sizes": clean_sizes,
        "number": number,
        "repeats": repeats,
        "seed": seed,
        "radius": R_MAX,
        "target_neighbors_excluding_self": TARGET_NEIGHBORS_EXCLUDING_SELF,
        "python": sys.version,
        "platform": platform.platform(),
        "processor": platform.processor(),
        "numpy": np.__version__,
        "scipy": scipy.__version__,
        "freud": getattr(freud_module, "__version__", None),
        "freud_threads": actual_threads,
        "freud_import_error": freud_import_error if not complete else None,
        "thread_environment": {
            key: os.environ.get(key)
            for key in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS")
        },
        "warning": "New measurements; absolute times are not the paper's data.",
    }
    metadata_path = output_dir / "run_metadata.json"
    metadata_path.write_text(json.dumps(metadata, indent=2, ensure_ascii=False),
                             encoding="utf-8")
    png, pdf = _plot(rows, output_dir, complete=complete)
    return {
        "rows": rows,
        "complete": complete,
        "csv": csv_path,
        "metadata": metadata_path,
        "png": png,
        "pdf": pdf,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sizes", nargs="+", type=int, default=list(DEFAULT_SIZES))
    parser.add_argument("--number", type=int, default=100,
                        help="complete build+query calls per repeat")
    parser.add_argument("--repeats", type=int, default=5)
    parser.add_argument("--threads", type=int, default=None,
                        help="freud thread count; omit to keep the library default")
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--allow-partial", action="store_true",
                        help="run SciPy only when freud is unavailable")
    parser.add_argument("--output-dir", type=Path,
                        default=Path(__file__).resolve().parent / "outputs")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    freud_module, import_error = _try_import_freud()
    try:
        result = run_benchmark(
            output_dir=args.output_dir,
            sizes=args.sizes,
            number=args.number,
            repeats=args.repeats,
            seed=args.seed,
            threads=args.threads,
            allow_partial=args.allow_partial,
            freud_module=freud_module,
            freud_import_error=import_error,
        )
    except (RuntimeError, ValueError) as exc:
        parser.error(str(exc))
    print(f"STATUS={'COMPLETE' if result['complete'] else 'PARTIAL_SCIPY_ONLY'}")
    print(f"CSV={result['csv']}")
    print(f"FIGURE={result['png']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

