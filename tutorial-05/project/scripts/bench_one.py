"""Run one neighbor search in a fresh process and emit one JSON record."""
from __future__ import annotations

import argparse
import json
import platform
import time

import numpy as np
import psutil
import scipy

try:
    import resource
except ImportError:  # pragma: no cover - Windows-specific branch
    resource = None

from src.neighbors import counts_dense, counts_kdtree, generate_positions


def peak_rss_mib():
    """Return the process high-water memory mark using platform conventions."""
    if resource is None:
        info = psutil.Process().memory_info()
        return float(getattr(info, "peak_wset", info.rss)) / 2**20
    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    if platform.system() == "Darwin":  # macOS reports bytes
        return float(peak) / 2**20
    return float(peak) / 1024  # Linux reports KiB


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--n", type=int, required=True)
    parser.add_argument("--method", choices=("dense", "kdtree"), required=True)
    parser.add_argument("--seed", type=int, default=20261116)
    parser.add_argument("--cutoff", type=float, default=3.0)
    args = parser.parse_args()

    if args.n < 0:
        parser.error("n must be nonnegative")
    if args.method == "dense" and args.n > 2500:
        parser.error("dense baseline intentionally capped at 2500 atoms")

    xyz, box = generate_positions(args.n, seed=args.seed)
    func = counts_dense if args.method == "dense" else counts_kdtree
    start = time.perf_counter()
    counts = func(xyz, box, args.cutoff)
    elapsed = time.perf_counter() - start

    print(
        json.dumps(
            {
                "n": args.n,
                "method": args.method,
                "wall_s": elapsed,
                "peak_rss_mib": peak_rss_mib(),
                "sum_coordination": int(counts.sum()),
                "mean_coordination": float(counts.mean()) if len(counts) else 0.0,
                "seed": args.seed,
                "cutoff_A": args.cutoff,
                "box_A": float(box[0]),
                "platform": platform.platform(),
                "python": platform.python_version(),
                "numpy": np.__version__,
                "scipy": scipy.__version__,
                "psutil": psutil.__version__,
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()

