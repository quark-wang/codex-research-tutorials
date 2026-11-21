"""Compare committed read-only Codex CLI probes with the deterministic resolver."""
from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.instructions import active_rule_ids, discover_project_instructions


SCOPES = ("root", "simulation", "analysis", "figures", "paper_reproduction", "reports")


def main() -> int:
    probe_dir = ROOT / "results/codex_instruction_probes"
    rows: list[dict[str, object]] = []
    for scope in SCOPES:
        path = probe_dir / f"{scope}.json"
        observed = json.loads(path.read_text(encoding="utf-8"))
        cwd = ROOT if scope == "root" else ROOT / scope
        expected = active_rule_ids(discover_project_instructions(ROOT, cwd))
        actual = observed.get("active_rule_ids", [])
        match = (
            observed.get("scope") == scope
            and actual == expected
            and len(actual) == len(set(actual))
            and observed.get("base_report_rule_loaded") is False
        )
        rows.append(
            {
                "scope": scope,
                "expected_count": len(expected),
                "observed_count": len(actual),
                "exact_order_match": match,
                "base_report_rule_loaded": observed.get("base_report_rule_loaded"),
                "expected_rule_ids": ";".join(expected),
                "observed_rule_ids": ";".join(actual),
            }
        )

    recorded_version = "codex-cli 0.171.0-alpha.13"
    try:
        version_run = subprocess.run(
            ["codex", "--version"], capture_output=True, text=True, check=False
        )
        replay_version = version_run.stdout.strip() or None
    except FileNotFoundError:
        replay_version = None
    passed = all(bool(row["exact_order_match"]) for row in rows)
    payload = {
        "schema_version": 1,
        "probe_type": "actual_codex_cli_read_only",
        "codex_version": recorded_version,
        "replay_codex_version": replay_version,
        "sandbox": "read-only",
        "ephemeral": True,
        "scopes": rows,
        "all_scopes_match_deterministic_resolver": passed,
    }
    target = ROOT / "results"
    (target / "codex_probe_summary.json").write_text(
        json.dumps(payload, indent=2) + "\n", encoding="utf-8"
    )
    pd.DataFrame(rows).to_csv(target / "codex_probe_summary.csv", index=False)
    print(f"Codex CLI probes: {'PASS' if passed else 'FAIL'} ({len(rows)} scopes)")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
