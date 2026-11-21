"""Run the release or quick 2D Ising workload and write chain summaries."""
from __future__ import annotations

import argparse
from hashlib import sha256
from itertools import product
import json
from pathlib import Path
import time

import pandas as pd

from simulation.core import derive_job_seeds, run_chain


ROOT = Path(__file__).resolve().parent
SIZES = (8, 12, 16, 24)
TEMPERATURES = (1.80, 1.95, 2.05, 2.15, 2.22, 2.27, 2.32, 2.40, 2.50, 2.65, 2.80)


def generate_table(
    sizes: tuple[int, ...] = SIZES,
    temperatures: tuple[float, ...] = TEMPERATURES,
    chains: int = 4,
    master_seed: int = 20261121,
    equilibration_sweeps: int = 600,
    measurement_sweeps: int = 1200,
    sample_interval: int = 4,
) -> pd.DataFrame:
    jobs = list(product(sizes, temperatures, range(chains)))
    seeds = derive_job_seeds(master_seed, len(jobs))
    rows = []
    for index, ((L, T, chain), seed) in enumerate(zip(jobs, seeds), start=1):
        rows.append(
            run_chain(L, T, chain, seed, equilibration_sweeps, measurement_sweeps, sample_interval).to_dict()
        )
        if index % 16 == 0 or index == len(jobs):
            print(f"completed {index}/{len(jobs)} chains")
    table = pd.DataFrame(rows).sort_values(["lattice_size", "temperature", "chain"])
    table.insert(0, "schema_version", 1)
    table["master_seed"] = int(master_seed)
    return table.reset_index(drop=True)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--quick", action="store_true")
    args = parser.parse_args()
    if args.output is None:
        args.output = (
            ROOT / "results/smoke/ising_chain_summary.csv"
            if args.quick
            else ROOT / "results/reproduction/ising_chain_summary.csv"
        )
    started = time.perf_counter()
    table = (
        generate_table((8, 12), (2.0, 2.27, 2.6), 2, 20261121, 40, 80, 4)
        if args.quick
        else generate_table()
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    table.to_csv(args.output, index=False, float_format="%.12g")
    elapsed = time.perf_counter() - started
    metadata = {
        "schema_version": 1,
        "data_kind": "synthetic_monte_carlo",
        "quick_workload": bool(args.quick),
        "rows": len(table),
        "sha256": sha256(args.output.read_bytes()).hexdigest(),
        "elapsed_seconds": elapsed,
        "note": "Wall time is machine-dependent; scientific rows are deterministic for the recorded seed and software path.",
    }
    args.output.with_suffix(".metadata.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {len(table)} rows to {args.output}")
    print(f"sha256={metadata['sha256']} elapsed={elapsed:.2f} s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
