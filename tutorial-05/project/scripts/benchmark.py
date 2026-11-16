"""Run reproducible benchmarks in independent subprocesses."""
from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
import json
import os
import platform
import statistics
import subprocess
import sys
from pathlib import Path

import numpy as np
import psutil
import scipy

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results"
DEFAULT_SIZES = [500, 1000, 2000, 5000, 10000, 30000]


def _run_trial(n, method, seed, cutoff, timeout):
    command = [
        sys.executable,
        "-m",
        "scripts.bench_one",
        "--n",
        str(n),
        "--method",
        method,
        "--seed",
        str(seed),
        "--cutoff",
        str(cutoff),
    ]
    completed = subprocess.run(
        command,
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=True,
    )
    return json.loads(completed.stdout.strip().splitlines()[-1])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--sizes", nargs="+", type=int, default=DEFAULT_SIZES)
    parser.add_argument("--seed", type=int, default=20261116)
    parser.add_argument("--cutoff", type=float, default=3.0)
    parser.add_argument("--timeout", type=float, default=180.0)
    args = parser.parse_args()
    if args.repeats < 1:
        parser.error("repeats must be positive")
    if not args.sizes or any(n < 1 for n in args.sizes):
        parser.error("sizes must be positive integers")

    OUT.mkdir(exist_ok=True)
    aggregate_rows = []
    raw_trials = []

    for n in args.sizes:
        methods = ("dense", "kdtree") if n <= 2000 else ("kdtree",)
        for method in methods:
            trials = [
                _run_trial(n, method, args.seed, args.cutoff, args.timeout)
                for _ in range(args.repeats)
            ]
            for index, trial in enumerate(trials, start=1):
                trial["trial"] = index
                raw_trials.append(trial)

            sums = {trial["sum_coordination"] for trial in trials}
            if len(sums) != 1:
                raise RuntimeError(f"nondeterministic coordination result: {n=} {method=}")

            elapsed = [float(trial["wall_s"]) for trial in trials]
            rss = [float(trial["peak_rss_mib"]) for trial in trials]
            row = {
                "n": n,
                "method": method,
                "median_wall_s": statistics.median(elapsed),
                "min_wall_s": min(elapsed),
                "max_wall_s": max(elapsed),
                "median_peak_rss_mib": statistics.median(rss),
                "min_peak_rss_mib": min(rss),
                "max_peak_rss_mib": max(rss),
                "mean_coordination": trials[0]["mean_coordination"],
                "sum_coordination": trials[0]["sum_coordination"],
                "repeats": args.repeats,
                "seed": args.seed,
                "cutoff_A": args.cutoff,
            }
            aggregate_rows.append(row)
            print(
                f"{n:>6} {method:<7} {row['median_wall_s']:.6f}s  "
                f"RSS {row['median_peak_rss_mib']:.1f} MiB",
                flush=True,
            )

    with (OUT / "benchmark.csv").open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(aggregate_rows[0]))
        writer.writeheader()
        writer.writerows(aggregate_rows)

    with (OUT / "benchmark_trials.jsonl").open("w", encoding="utf-8") as file:
        for trial in raw_trials:
            file.write(json.dumps(trial, sort_keys=True) + "\n")

    environment = {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "python": sys.version,
        "platform": platform.platform(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "logical_cpu_count": psutil.cpu_count(logical=True),
        "physical_cpu_count": psutil.cpu_count(logical=False),
        "numpy": np.__version__,
        "scipy": scipy.__version__,
        "psutil": psutil.__version__,
        "thread_environment": {
            key: os.environ.get(key)
            for key in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS")
        },
        "sizes": args.sizes,
        "repeats": args.repeats,
        "seed": args.seed,
        "cutoff_A": args.cutoff,
        "purpose": "Synthetic uniform particles; orthorhombic PBC",
        "warning": "Dense method intentionally not run above 2,000 atoms.",
    }
    (OUT / "environment.json").write_text(
        json.dumps(environment, indent=2), encoding="utf-8"
    )


if __name__ == "__main__":
    main()

