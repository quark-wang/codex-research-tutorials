"""Profile identical N=2,000 configurations and save hotspot reports."""
from __future__ import annotations

import cProfile
import io
import json
import pstats
from pathlib import Path

from src.neighbors import counts_dense, counts_kdtree, generate_positions

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results"


def main():
    OUT.mkdir(exist_ok=True)
    xyz, box = generate_positions(2000)
    summary = {}

    for name, func in (("dense", counts_dense), ("kdtree", counts_kdtree)):
        profiler = cProfile.Profile()
        profiler.enable()
        result = func(xyz, box, 3.0)
        profiler.disable()

        profiler.dump_stats(str(OUT / f"profile_{name}.prof"))
        report = io.StringIO()
        stats = pstats.Stats(profiler, stream=report).strip_dirs()
        stats.sort_stats(pstats.SortKey.CUMULATIVE).print_stats(20)
        (OUT / f"profile_{name}.txt").write_text(
            report.getvalue(), encoding="utf-8"
        )
        summary[name] = {
            "total_calls": int(stats.total_calls),
            "primitive_calls": int(stats.prim_calls),
            "total_time_s": float(stats.total_tt),
            "mean_coordination": float(result.mean()),
            "sum_coordination": int(result.sum()),
        }
        print(
            f"{name}: profile total={stats.total_tt:.6f}s, "
            f"mean coordination={result.mean():.3f}"
        )

    (OUT / "profile_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )


if __name__ == "__main__":
    main()

