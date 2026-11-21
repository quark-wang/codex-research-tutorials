from pathlib import Path

import pytest

from src.instructions import active_rule_ids, discover_project_instructions
from src.policy import audit_paths
from src.raw_guard import hash_tree, verify_manifest, write_manifest


ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("scope,expected", [
    ("simulation", "simulation/AGENTS.md"),
    ("analysis", "analysis/AGENTS.md"),
    ("figures", "figures/AGENTS.md"),
    ("paper_reproduction", "paper_reproduction/AGENTS.md"),
    ("reports", "reports/AGENTS.override.md"),
])
def test_nested_instruction_chain(scope, expected):
    sources = discover_project_instructions(ROOT, ROOT / scope)
    assert [s.relative_path for s in sources] == ["AGENTS.md", expected]


def test_report_override_shadows_same_directory_agents():
    sources = discover_project_instructions(ROOT, ROOT / "reports")
    rules = active_rule_ids(sources)
    assert "REPORT-SOURCE-01" in rules
    assert "REPORT-BASE-IGNORED" not in rules


def test_root_scope_loads_only_root_file():
    sources = discover_project_instructions(ROOT, ROOT)
    assert [s.relative_path for s in sources] == ["AGENTS.md"]


def test_discovery_rejects_outside_directory(tmp_path):
    with pytest.raises(ValueError):
        discover_project_instructions(ROOT, tmp_path)


def test_safe_analysis_change_passes():
    result = audit_paths("analysis", ["analysis/observables.py", "tests/test_analysis.py"])
    assert result["passed"]


def test_raw_edit_fails_in_every_scope():
    for scope in ("root", "simulation", "analysis", "figures", "paper_reproduction", "reports"):
        assert not audit_paths(scope, ["data/raw/ising_chain_summary.csv"])["passed"]


def test_report_scope_cannot_edit_analysis():
    result = audit_paths("reports", ["analysis/observables.py"])
    assert not result["passed"]
    assert result["findings"][0]["code"] == "REPORTS_SCOPE"


def test_report_generated_file_passes():
    assert audit_paths("reports", ["reports/generated/summary.md"])["passed"]


def test_policy_rejects_parent_traversal():
    with pytest.raises(ValueError):
        audit_paths("root", ["../secret.txt"])


def test_raw_manifest_detects_change(tmp_path):
    raw = tmp_path / "raw"
    raw.mkdir()
    sample = raw / "x.csv"
    sample.write_text("a,b\n1,2\n", encoding="utf-8")
    manifest = tmp_path / "manifest.json"
    write_manifest(raw, manifest)
    assert verify_manifest(raw, manifest)["passed"]
    sample.write_text("a,b\n1,3\n", encoding="utf-8")
    check = verify_manifest(raw, manifest)
    assert not check["passed"]
    assert check["changed"] == ["x.csv"]


def test_hash_tree_is_deterministic(tmp_path):
    (tmp_path / "b.txt").write_text("b", encoding="utf-8")
    (tmp_path / "a.txt").write_text("a", encoding="utf-8")
    assert hash_tree(tmp_path) == hash_tree(tmp_path)
    assert list(hash_tree(tmp_path)) == ["a.txt", "b.txt"]
