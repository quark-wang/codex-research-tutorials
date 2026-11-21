"""Execute the release evidence chain and save all observed outputs."""
from __future__ import annotations

import json
from hashlib import sha256
import platform
from pathlib import Path
import re
import subprocess
import sys
import time

import matplotlib
import numpy
import pandas
import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from analysis.observables import load_chain_table, write_analysis
from scripts.build_audits import main as build_audits
from src.raw_guard import verify_manifest


def run(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=ROOT, text=True, capture_output=True, check=False)


def verify_paper_reproduction() -> dict[str, object]:
    """Validate the committed Saratz Figure 9(a-b) independent reproduction."""
    paper_root = ROOT / "paper_reproduction"
    chain_path = paper_root / "results/reproduction/figure9_chain_summary.csv"
    summary_path = paper_root / "results/reproduction/figure9_summary.csv"
    metadata_path = paper_root / "results/reproduction/figure9_metadata.json"
    required_paths = [chain_path, summary_path, metadata_path]
    if not all(path.is_file() for path in required_paths):
        return {"passed": False, "error": "missing paper-reproduction table or metadata"}
    try:
        chains = pandas.read_csv(chain_path)
        summary = pandas.read_csv(summary_path)
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        group_counts = chains.groupby(["lattice_size", "temperature"])["chain"].nunique()
        sizes = sorted(int(value) for value in chains["lattice_size"].unique())
        temperatures = sorted(float(value) for value in chains["temperature"].unique())
        tc = float(metadata["exact_reference"]["Tc"])
        above = summary.loc[summary["temperature"] >= tc, "m_L_over_m_infinity"]
        tails = summary.loc[numpy.isclose(summary["temperature"], 3.0), ["lattice_size", "m_L_mean"]]
        tail_values = {int(row.lattice_size): float(row.m_L_mean) for row in tails.itertuples()}
        low = summary.loc[summary["temperature"] <= 2.0]
        low_mae = float(numpy.mean(numpy.abs(low["m_L_mean"] - low["m_infinity_exact"])))

        hash_checks: dict[str, bool] = {}
        file_sizes: dict[str, int] = {}
        for key in ("source_script", "chain_csv", "summary_csv", "png", "pdf"):
            record = metadata["files"][key]
            target = (paper_root / record["path"]).resolve()
            target.relative_to(paper_root.resolve())
            exists = target.is_file()
            hash_checks[key] = bool(
                exists and sha256(target.read_bytes()).hexdigest() == record["sha256"]
            )
            file_sizes[key] = target.stat().st_size if exists else 0

        schema_passed = bool(
            len(chains) == 732
            and len(summary) == 183
            and sizes == [10, 20, 40]
            and len(temperatures) == 61
            and set(group_counts) == {4}
            and chains["seed"].nunique() == len(chains)
            and not summary.duplicated(["lattice_size", "temperature"]).any()
            and set(summary["schema_version"]) == {1}
            and set(summary["master_seed"]) == {20261121}
            and set(summary["model"]) == {"2d_square_ising_zero_field"}
            and set(summary["magnetization_estimator"]) == {"mean_abs_M_over_L2"}
        )
        ratio_filter_passed = bool(len(above) > 0 and above.isna().all())
        finite_size_order_passed = bool(
            set(tail_values) == {10, 20, 40}
            and tail_values[10] > tail_values[20] > tail_values[40]
        )
        artifact_passed = bool(
            all(hash_checks.values())
            and file_sizes["png"] > 10_000
            and file_sizes["pdf"] > 1_000
        )
        passed = bool(
            schema_passed
            and ratio_filter_passed
            and finite_size_order_passed
            and artifact_passed
            and low_mae < 0.005
            and metadata["reproduction_class"] == "independent_method_reproduction"
            and not metadata["quick_non_scientific_run"]
        )
        return {
            "passed": passed,
            "schema_passed": schema_passed,
            "ratio_filter_passed": ratio_filter_passed,
            "finite_size_order_at_T_3_passed": finite_size_order_passed,
            "artifact_hashes_passed": artifact_passed,
            "hash_checks": hash_checks,
            "chain_rows": len(chains),
            "summary_rows": len(summary),
            "lattice_sizes": sizes,
            "temperature_count": len(temperatures),
            "chains_per_state_point": int(group_counts.iloc[0]),
            "mean_absolute_difference_from_onsager_for_T_le_2": low_mae,
            "m_L_at_T_3": {str(key): value for key, value in tail_values.items()},
        }
    except Exception as error:  # verification must record a structured failure
        return {"passed": False, "error": f"{type(error).__name__}: {error}"}


def main() -> int:
    started = time.perf_counter()
    results = ROOT / "results"
    results.mkdir(exist_ok=True)

    test = run([sys.executable, "-m", "pytest", "-q"])
    (results / "pytest_output.txt").write_text(test.stdout + test.stderr, encoding="utf-8")
    match = re.search(r"(\d+) passed", test.stdout)
    tests_passed = int(match.group(1)) if match and test.returncode == 0 else 0

    critical = write_analysis(ROOT / "data/raw/ising_chain_summary.csv", results)
    build_audits()
    probe_check = run([sys.executable, "scripts/summarize_codex_probes.py"])
    (results / "codex_probe_check_output.txt").write_text(
        probe_check.stdout + probe_check.stderr, encoding="utf-8"
    )
    probe_summary = json.loads(
        (results / "codex_probe_summary.json").read_text(encoding="utf-8")
    )
    raw_check = verify_manifest(ROOT / "data/raw", ROOT / "data/raw_manifest.json")
    frame = load_chain_table(ROOT / "data/raw/ising_chain_summary.csv")
    group_counts = frame.groupby(["lattice_size", "temperature"])["chain"].nunique()
    schema_passed = bool(
        len(frame) == 176
        and sorted(frame.lattice_size.unique().tolist()) == [8, 12, 16, 24]
        and frame.temperature.nunique() == 11
        and set(group_counts) == {4}
        and frame.seed.nunique() == len(frame)
        and set(frame.n_samples) == {300}
    )
    reproduction_path = results / "reproduction/ising_chain_summary.csv"
    released_path = ROOT / "data/raw/ising_chain_summary.csv"
    reproduction_match = bool(
        reproduction_path.is_file()
        and sha256(reproduction_path.read_bytes()).hexdigest() == sha256(released_path.read_bytes()).hexdigest()
    )
    policy = json.loads((results / "policy_scenarios.json").read_text(encoding="utf-8"))["scenarios"]
    instruction = json.loads((results / "instruction_resolution.json").read_text(encoding="utf-8"))["scopes"]
    paper_check = verify_paper_reproduction()
    verification = {
        "schema_version": 1,
        "data_kind": "synthetic_monte_carlo",
        "tests_passed": tests_passed,
        "pytest_exit_code": test.returncode,
        "raw_hash_passed": raw_check["passed"],
        "schema_passed": schema_passed,
        "chain_rows": len(frame),
        "lattice_sizes": sorted(int(v) for v in frame.lattice_size.unique()),
        "temperatures": sorted(float(v) for v in frame.temperature.unique()),
        "chains_per_state_point": int(group_counts.iloc[0]),
        "samples_per_chain": int(frame.n_samples.iloc[0]),
        "reproduction_matches_release_sha256": reproduction_match,
        "instruction_scopes": len(instruction),
        "codex_probe_passed": bool(
            probe_check.returncode == 0
            and probe_summary["all_scopes_match_deterministic_resolver"]
        ),
        "codex_version": probe_summary["codex_version"],
        "policy_scenarios_checked": len(policy),
        "policy_outcomes": {item["scenario"]: item["passed"] for item in policy},
        "paper_reproduction": paper_check,
        "expected_figure_pairs": 7,
        "critical_estimates": {
            "exact_tc_reference": critical["exact_tc_reduced"],
            "largest_size_chi_peak": critical["susceptibility_peak"]["temperature_estimate"],
            "binder_median": critical["binder_median_temperature"],
        },
        "environment": {
            "python": platform.python_version(), "platform": platform.platform(),
            "numpy": numpy.__version__, "pandas": pandas.__version__,
            "matplotlib": matplotlib.__version__, "pytest": pytest.__version__,
        },
    }
    (results / "verification_summary.json").write_text(json.dumps(verification, indent=2) + "\n", encoding="utf-8")

    figures = run([sys.executable, "make_figures.py"])
    (results / "figure_generation_output.txt").write_text(figures.stdout + figures.stderr, encoding="utf-8")
    png = sorted((results / "figures").glob("fig*.png"))
    pdf = sorted((results / "figures").glob("fig*.pdf"))
    figure_passed = figures.returncode == 0 and len(png) == len(pdf) == 7 and all(p.stat().st_size > 1000 for p in png + pdf)

    report_dir = ROOT / "reports/generated"
    report_dir.mkdir(parents=True, exist_ok=True)
    report = (
        "# Release evidence summary\n\n"
        "This report uses deterministic **synthetic Monte Carlo** data for the two-dimensional Ising model in **reduced units**. "
        "Uncertainty bars are SEM across **independent chains** and are not autocorrelation-corrected production uncertainties.\n\n"
        f"- Exact reference Tc: {critical['exact_tc_reduced']:.9f}\n"
        f"- Largest-size susceptibility-peak estimate: {critical['susceptibility_peak']['temperature_estimate']:.6f}\n"
        f"- Median Binder-crossing estimate: {critical['binder_median_temperature']:.6f}\n"
        f"- Automated tests: {tests_passed} passed\n"
        f"- Raw SHA-256 verification: {'PASS' if raw_check['passed'] else 'FAIL'}\n"
        f"- Saratz Figure 9(a-b) independent reproduction: {'PASS' if paper_check['passed'] else 'FAIL'}\n"
    )
    (report_dir / "RELEASE_REPORT.md").write_text(report, encoding="utf-8")
    report_check = run([sys.executable, "scripts/check_report.py"])
    (results / "report_check_output.txt").write_text(report_check.stdout + report_check.stderr, encoding="utf-8")

    verification.update({
        "figure_generation_exit_code": figures.returncode,
        "figure_pairs_created": len(png),
        "figure_verification_passed": figure_passed,
        "report_check_exit_code": report_check.returncode,
        "elapsed_seconds": time.perf_counter() - started,
    })
    (results / "verification_summary.json").write_text(json.dumps(verification, indent=2) + "\n", encoding="utf-8")
    print(test.stdout.strip())
    print(figures.stdout.strip())
    print(report_check.stdout.strip())
    print(f"raw hash: {'PASS' if raw_check['passed'] else 'FAIL'}; schema: {'PASS' if schema_passed else 'FAIL'}")
    print(f"paper reproduction: {'PASS' if paper_check['passed'] else 'FAIL'}")
    print(f"release verification elapsed: {verification['elapsed_seconds']:.2f} s")
    passed = (
        test.returncode == 0
        and raw_check["passed"]
        and schema_passed
        and reproduction_match
        and verification["codex_probe_passed"]
        and paper_check["passed"]
        and figure_passed
        and report_check.returncode == 0
    )
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
