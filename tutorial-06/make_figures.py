"""Generate seven release figures from committed result tables (no simulation)."""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parent
RESULTS = ROOT / "results"
OUT = RESULTS / "figures"
PALETTE = ["#0072B2", "#E69F00", "#009E73", "#CC79A7", "#D55E00"]


def style() -> None:
    plt.rcParams.update({
        "font.family": "DejaVu Sans", "font.size": 10,
        "axes.spines.top": False, "axes.spines.right": False,
        "axes.linewidth": 0.9, "axes.grid": True, "grid.alpha": 0.2,
        "grid.linewidth": 0.7, "xtick.direction": "out", "ytick.direction": "out",
        "legend.frameon": False, "figure.facecolor": "white", "axes.facecolor": "#FCFCFD",
        "savefig.bbox": "tight",
    })


def save(fig: plt.Figure, stem: str) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT / f"{stem}.png", dpi=300, facecolor="white")
    fig.savefig(OUT / f"{stem}.pdf", facecolor="white")
    plt.close(fig)


def instruction_chain() -> None:
    payload = json.loads((RESULTS / "instruction_resolution.json").read_text(encoding="utf-8"))
    probes = json.loads((RESULTS / "codex_probe_summary.json").read_text(encoding="utf-8"))
    probe_matches = {row["scope"]: row["exact_order_match"] for row in probes["scopes"]}
    fig, ax = plt.subplots(figsize=(12.0, 5.2))
    ax.set_xlim(0, 12); ax.set_ylim(0, 6); ax.axis("off")
    root_box = FancyBboxPatch((4.6, 4.65), 2.8, 0.75, boxstyle="round,pad=0.12", fc="#DCEAF7", ec="#0072B2", lw=1.5)
    ax.add_patch(root_box)
    root_status = "MATCH" if probe_matches["root"] else "MISMATCH"
    ax.text(6, 5.08, f"Repository root\nAGENTS.md · 5 shared rules\nCLI probe: {root_status}",
            ha="center", va="center", weight="bold")
    scopes = ["simulation", "analysis", "figures", "paper_reproduction", "reports"]
    xs = [0.10, 2.45, 4.80, 7.15, 9.50]
    colors = PALETTE
    for x, scope, color in zip(xs, scopes, colors):
        info = payload["scopes"][scope]
        source = info["sources"][-1]
        box = FancyBboxPatch((x, 1.35), 2.20, 1.45, boxstyle="round,pad=0.12", fc="#FFFFFF", ec=color, lw=1.5)
        ax.add_patch(box)
        ax.add_patch(FancyArrowPatch((6, 4.65), (x + 1.1, 2.85), arrowstyle="-|>", mutation_scale=12, color="#667085", lw=1.1))
        filename = Path(source).name
        status = "MATCH" if probe_matches[scope] else "MISMATCH"
        ax.text(x + 1.1, 2.23, f"{scope}/\n{filename}\n{len(info['rule_ids'])} active rules\nCLI probe: {status}",
                ha="center", va="center", fontsize=7.9, weight="bold")
    ax.text(6, 0.55, "Deterministic resolver + actual read-only CLI probes; same-directory override wins",
            ha="center", color="#475467")
    ax.set_title("Layered AGENTS.md instruction chain", weight="bold", pad=12, fontsize=16)
    save(fig, "fig01_instruction_hierarchy")


def curves(metric: str, sem: str, ylabel: str, title: str, stem: str, critical: dict, peak=False) -> None:
    data = pd.read_csv(RESULTS / "thermodynamic_summary.csv")
    fig, ax = plt.subplots(figsize=(7.2, 4.8))
    for color, (L, group) in zip(PALETTE, data.groupby("lattice_size")):
        ax.errorbar(group.temperature, group[metric], yerr=group[sem], label=f"L = {int(L)}", color=color,
                    marker="o", ms=4.2, lw=1.5, capsize=2.5)
    exact = critical["exact_tc_reduced"]
    ax.axvline(exact, color="#344054", ls="--", lw=1.2, label=r"Exact $T_c$ = 2.2692")
    if peak:
        p = critical["susceptibility_peak"]
        ax.axvline(p["temperature_estimate"], color="#D55E00", ls=":", lw=1.4,
                   label=f"L={p['lattice_size']} peak = {p['temperature_estimate']:.3f}")
    ax.set(xlabel=r"Temperature $T$ ($J/k_B$)", ylabel=ylabel, title=title)
    ax.legend(ncol=2, fontsize=8.5)
    fig.tight_layout()
    save(fig, stem)


def binder(critical: dict) -> None:
    data = pd.read_csv(RESULTS / "thermodynamic_summary.csv")
    fig, ax = plt.subplots(figsize=(7.2, 4.8))
    for color, (L, group) in zip(PALETTE, data.groupby("lattice_size")):
        ax.errorbar(group.temperature, group.binder_u4_mean, yerr=group.binder_u4_sem,
                    color=color, marker="o", ms=4.2, lw=1.5, capsize=2.5, label=f"L = {int(L)}")
    exact = critical["exact_tc_reduced"]
    ax.axvline(exact, color="#344054", ls="--", lw=1.2, label=r"Exact $T_c$")
    crossing_lines = []
    for crossing in critical["binder_crossings"]:
        x = crossing["temperature_estimate"]
        ax.axvline(x, color="#98A2B3", alpha=0.5, lw=0.8)
        crossing_lines.append(f"L={crossing['L_low']}/{crossing['L_high']}: {x:.3f}")
    ax.text(0.98, 0.96, "Binder crossings\n" + "\n".join(crossing_lines), transform=ax.transAxes,
            ha="right", va="top", fontsize=8.2, color="#475467",
            bbox={"boxstyle": "round,pad=0.35", "facecolor": "white", "edgecolor": "#D0D5DD", "alpha": 0.92})
    ax.set(xlabel=r"Temperature $T$ ($J/k_B$)", ylabel=r"Binder cumulant $U_4$",
           title="Binder cumulant crossings across lattice sizes")
    ax.set_ylim(0.30, 0.70)
    ax.legend(ncol=2, fontsize=8.5, loc="lower left")
    fig.tight_layout()
    save(fig, "fig06_binder_crossings")


def verification_dashboard() -> None:
    payload = json.loads((RESULTS / "verification_summary.json").read_text(encoding="utf-8"))
    labels = ["pytest", "raw SHA-256", "schema", "Codex CLI probes", "paper reproduction", "instruction scopes", "policy scenarios", "base figure pairs"]
    values = [
        payload["tests_passed"], payload["raw_hash_passed"], payload["schema_passed"], payload["codex_probe_passed"],
        payload["paper_reproduction"]["passed"], payload["instruction_scopes"],
        payload["policy_scenarios_checked"], payload["expected_figure_pairs"],
    ]
    display = [str(values[0]), "PASS" if values[1] else "FAIL", "PASS" if values[2] else "FAIL",
               "PASS" if values[3] else "FAIL", "PASS" if values[4] else "FAIL",
               str(values[5]), str(values[6]), str(values[7])]
    ok = [values[0] > 0, bool(values[1]), bool(values[2]), bool(values[3]), bool(values[4]),
          values[5] == 6, values[6] == 4, values[7] == 7]
    fig, ax = plt.subplots(figsize=(9.0, 5.1))
    y = np.arange(len(labels))[::-1]
    colors = ["#009E73" if passed else "#D55E00" for passed in ok]
    ax.barh(y, np.ones(len(y)), color=colors, alpha=0.16, edgecolor=colors, height=0.62)
    for yi, label, value, passed in zip(y, labels, display, ok):
        ax.text(0.03, yi, label, va="center", ha="left", weight="bold", color="#344054")
        ax.text(0.97, yi, value, va="center", ha="right", weight="bold", color="#027A48" if passed else "#B42318")
    ax.set_xlim(0, 1); ax.set_ylim(-0.7, len(labels) - 0.3); ax.axis("off")
    ax.set_title("Release verification dashboard", weight="bold", pad=12)
    ax.text(0.5, -0.55, "AGENTS.md supplies durable guidance; executable checks supply enforcement evidence.",
            ha="center", color="#475467")
    fig.tight_layout()
    save(fig, "fig07_verification_dashboard")


def main() -> int:
    style()
    critical = json.loads((RESULTS / "critical_summary.json").read_text(encoding="utf-8"))
    instruction_chain()
    curves("abs_magnetization_per_spin_mean", "abs_magnetization_per_spin_sem", r"$\langle |M| \rangle/N$",
           "Finite-size magnetization", "fig02_magnetization", critical)
    curves("energy_per_spin_mean", "energy_per_spin_sem", r"$\langle E \rangle/N$ ($J$)",
           "Energy per spin", "fig03_energy", critical)
    curves("heat_capacity_per_spin_mean", "heat_capacity_per_spin_sem", r"$C_V/N$ ($k_B$)",
           "Heat-capacity anomaly", "fig04_heat_capacity", critical)
    curves("susceptibility_abs_per_spin_mean", "susceptibility_abs_per_spin_sem", r"$\chi_{|M|}/N$",
           "Susceptibility peak and finite-size shift", "fig05_susceptibility", critical, peak=True)
    binder(critical)
    verification_dashboard()
    rows = []
    for png in sorted(OUT.glob("*.png")):
        pdf = png.with_suffix(".pdf")
        rows.append({"figure": png.stem, "png": png.relative_to(ROOT).as_posix(), "pdf": pdf.relative_to(ROOT).as_posix(),
                     "png_bytes": png.stat().st_size, "pdf_bytes": pdf.stat().st_size})
    pd.DataFrame(rows).to_csv(RESULTS / "figure_manifest.csv", index=False)
    print(f"wrote {len(rows)} PNG/PDF figure pairs to {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
