from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from analysis.observables import write_analysis


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=ROOT / "data/raw/ising_chain_summary.csv")
    parser.add_argument("--output", type=Path, default=ROOT / "results")
    args = parser.parse_args()
    result = write_analysis(args.input, args.output)
    peak = result["susceptibility_peak"]
    print(f"chi peak (L={peak['lattice_size']}): T={peak['temperature_estimate']:.5f}")
    print(f"Binder crossing median: T={result['binder_median_temperature']}")
    print(f"exact Tc reference: T={result['exact_tc_reduced']:.9f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
