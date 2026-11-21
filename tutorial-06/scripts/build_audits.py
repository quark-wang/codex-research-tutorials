"""Write instruction-resolution and mechanical scope-audit evidence."""
from __future__ import annotations

import json
from pathlib import Path
import sys

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.instructions import active_rule_ids, discover_project_instructions
from src.policy import audit_paths


SCOPES = ("root", "simulation", "analysis", "figures", "paper_reproduction", "reports")
SCENARIOS = {
    "safe_analysis_patch": ("analysis", ["analysis/observables.py", "tests/test_analysis.py"]),
    "raw_snapshot_tamper": ("simulation", ["data/raw/ising_chain_summary.csv"]),
    "report_scope_escape": ("reports", ["analysis/observables.py"]),
    "safe_figure_export": ("figures", ["results/figures/fig02_magnetization.png"]),
}


def main() -> int:
    target = ROOT / "results"
    target.mkdir(exist_ok=True)
    rows, payload = [], {"schema_version": 1, "scopes": {}}
    for scope in SCOPES:
        cwd = ROOT if scope == "root" else ROOT / scope
        sources = discover_project_instructions(ROOT, cwd)
        rules = active_rule_ids(sources)
        payload["scopes"][scope] = {
            "working_directory": "." if scope == "root" else scope,
            "sources": [item.relative_path for item in sources],
            "rule_ids": rules,
        }
        for order, source in enumerate(sources, start=1):
            rows.append({
                "scope": scope, "order": order, "source": source.relative_path,
                "rule_count": len(source.rule_ids), "rule_ids": ";".join(source.rule_ids),
            })
    pd.DataFrame(rows).to_csv(target / "instruction_resolution.csv", index=False)
    (target / "instruction_resolution.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    results = []
    for name, (scope, paths) in SCENARIOS.items():
        audit = audit_paths(scope, paths)
        audit["scenario"] = name
        results.append(audit)
    (target / "policy_scenarios.json").write_text(json.dumps({"scenarios": results}, indent=2) + "\n", encoding="utf-8")
    pd.DataFrame([
        {
            "scenario": item["scenario"], "scope": item["scope"],
            "passed": item["passed"], "changed_paths": ";".join(item["changed_paths"]),
            "finding_codes": ";".join(f["code"] for f in item["findings"]),
        }
        for item in results
    ]).to_csv(target / "policy_scenarios.csv", index=False)
    print(f"wrote instruction evidence for {len(SCOPES)} scopes and {len(results)} audit scenarios")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
