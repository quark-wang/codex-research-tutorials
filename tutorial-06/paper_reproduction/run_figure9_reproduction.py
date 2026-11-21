"""Independent method reproduction of Saratz et al. (2016), Figure 9(a-b).

The published bitmap and numerical data are not used.  This script samples the
same finite-size zero-field Ising target with declared tutorial parameters,
then recreates the two scientific relationships using new Monte Carlo data.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import platform
from pathlib import Path
import sys
import time
from typing import Callable

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

try:
    import numba
    from numba import njit

    NUMBA_AVAILABLE = True
    NUMBA_VERSION = numba.__version__
except ImportError:  # pragma: no cover - exercised only in minimal environments
    NUMBA_AVAILABLE = False
    NUMBA_VERSION = None

    def njit(*_args: object, **_kwargs: object) -> Callable:  # type: ignore[misc]
        def decorate(function: Callable) -> Callable:
            return function

        return decorate


HERE = Path(__file__).resolve().parent
PAPER_DOI = "10.1038/ncomms13611"
PAPER_URL = "https://www.nature.com/articles/ncomms13611"
SIZES = (10, 20, 40)
MASTER_SEED = 20261121
CHAINS = 4
EQUILIBRATION_SWEEPS = 3_000
MEASUREMENT_SWEEPS = 9_000
SAMPLE_INTERVAL = 9
NU = 1.0


def publication_temperatures() -> tuple[float, ...]:
    """A declared grid covering the paper's range and resolving the critical region."""
    low = np.arange(1.50, 2.10, 0.05)
    critical = np.arange(2.10, 2.45, 0.01)
    high = np.arange(2.45, 3.001, 0.05)
    # Two additional subcritical points resolve the rapidly changing FSS ratio
    # without pretending that this tutorial grid was published by the authors.
    near_tc = np.array([2.265, 2.268])
    values = np.unique(np.round(np.concatenate((low, critical, near_tc, high)), 8))
    return tuple(float(value) for value in values)


TEMPERATURES = publication_temperatures()


def exact_tc() -> float:
    """Onsager critical temperature in reduced units J/k_B."""
    return float(2.0 / np.log(1.0 + np.sqrt(2.0)))


def onsager_magnetization(temperature: np.ndarray | float) -> np.ndarray:
    """Infinite-lattice spontaneous magnetization for the square Ising model."""
    values = np.asarray(temperature, dtype=float)
    result = np.zeros_like(values)
    ordered = values < exact_tc()
    if np.any(ordered):
        sinh_term = np.sinh(2.0 / values[ordered])
        result[ordered] = np.power(np.maximum(0.0, 1.0 - sinh_term ** -4), 0.125)
    return result


@njit(cache=False)
def _random_unit(state: np.ndarray) -> float:
    """Deterministic xorshift64* variate in [0,1), independent of global RNG state."""
    x = state[0]
    x ^= x >> np.uint64(12)
    x ^= x << np.uint64(25)
    x ^= x >> np.uint64(27)
    state[0] = x
    value = x * np.uint64(2685821657736338717)
    return float(value >> np.uint64(11)) * (1.0 / 9007199254740992.0)


@njit(cache=False)
def _run_chain_kernel(
    lattice_size: int,
    temperature: float,
    seed: np.uint64,
    equilibration_sweeps: int,
    measurement_sweeps: int,
    sample_interval: int,
) -> tuple[float, float, float, float, int]:
    """Run an ordered-start red-black Metropolis chain on an even periodic lattice."""
    spins = np.ones((lattice_size, lattice_size), dtype=np.int8)
    state = np.empty(1, dtype=np.uint64)
    state[0] = seed if seed != 0 else np.uint64(0x9E3779B97F4A7C15)
    beta = 1.0 / temperature
    total_sweeps = equilibration_sweeps + measurement_sweeps
    accepted = 0
    attempted = 0
    sum_abs_m = 0.0
    sum_m2 = 0.0
    sum_m4 = 0.0
    n_samples = 0

    for sweep in range(total_sweeps):
        for parity in range(2):
            for i in range(lattice_size):
                first_j = (parity - i) & 1
                for j in range(first_j, lattice_size, 2):
                    spin = int(spins[i, j])
                    neighbor_sum = (
                        int(spins[(i - 1) % lattice_size, j])
                        + int(spins[(i + 1) % lattice_size, j])
                        + int(spins[i, (j - 1) % lattice_size])
                        + int(spins[i, (j + 1) % lattice_size])
                    )
                    delta_energy = 2 * spin * neighbor_sum
                    attempted += 1
                    if delta_energy <= 0 or _random_unit(state) < math.exp(-beta * delta_energy):
                        spins[i, j] = np.int8(-spin)
                        accepted += 1

        measurement_index = sweep - equilibration_sweeps + 1
        if measurement_index > 0 and measurement_index % sample_interval == 0:
            magnetization = 0
            for i in range(lattice_size):
                for j in range(lattice_size):
                    magnetization += int(spins[i, j])
            magnitude = float(abs(magnetization))
            sum_abs_m += magnitude
            sum_m2 += float(magnetization * magnetization)
            sum_m4 += float(magnetization * magnetization) ** 2
            n_samples += 1

    return (
        sum_abs_m / n_samples,
        sum_m2 / n_samples,
        sum_m4 / n_samples,
        accepted / attempted,
        n_samples,
    )


def run_chain(
    lattice_size: int,
    temperature: float,
    seed: int,
    equilibration_sweeps: int,
    measurement_sweeps: int,
    sample_interval: int,
) -> dict[str, int | float | str]:
    """Validated Python wrapper around the deterministic compiled kernel."""
    L = int(lattice_size)
    T = float(temperature)
    if L < 4 or L % 2:
        raise ValueError("red-black periodic updates require an even lattice size >= 4")
    if not np.isfinite(T) or T <= 0:
        raise ValueError("temperature must be positive and finite")
    if equilibration_sweeps < 0 or measurement_sweeps <= 0 or sample_interval <= 0:
        raise ValueError("invalid sampling counts")
    if measurement_sweeps < sample_interval:
        raise ValueError("measurement budget stores no samples")
    mean_abs_m, mean_m2, mean_m4, acceptance, n_samples = _run_chain_kernel(
        L,
        T,
        np.uint64(int(seed)),
        int(equilibration_sweeps),
        int(measurement_sweeps),
        int(sample_interval),
    )
    return {
        "lattice_size": L,
        "temperature": T,
        "seed": int(seed),
        "equilibration_sweeps": int(equilibration_sweeps),
        "measurement_sweeps": int(measurement_sweeps),
        "sample_interval": int(sample_interval),
        "n_samples": int(n_samples),
        "mean_abs_M": float(mean_abs_m),
        "mean_M2": float(mean_m2),
        "mean_M4": float(mean_m4),
        "acceptance_fraction": float(acceptance),
        "data_kind": "synthetic_monte_carlo",
        "model": "2d_square_ising_zero_field",
        "initial_state": "ordered_up",
        "update_algorithm": "red_black_metropolis",
    }


def derive_seeds(master_seed: int, count: int) -> list[int]:
    children = np.random.SeedSequence(int(master_seed)).spawn(int(count))
    seeds: list[int] = []
    for child in children:
        words = child.generate_state(2, dtype=np.uint32)
        seed = (int(words[0]) << 32) | int(words[1])
        seeds.append(seed or 1)
    if len(set(seeds)) != len(seeds):
        raise RuntimeError("unexpected seed collision")
    return seeds


def generate_chains(
    sizes: tuple[int, ...],
    temperatures: tuple[float, ...],
    chains: int,
    master_seed: int,
    equilibration_sweeps: int,
    measurement_sweeps: int,
    sample_interval: int,
) -> pd.DataFrame:
    jobs = [(L, T, chain) for L in sizes for T in temperatures for chain in range(chains)]
    seeds = derive_seeds(master_seed, len(jobs))
    rows: list[dict[str, int | float | str]] = []
    for index, ((L, T, chain), seed) in enumerate(zip(jobs, seeds), start=1):
        row = run_chain(L, T, seed, equilibration_sweeps, measurement_sweeps, sample_interval)
        row["chain"] = chain
        row["master_seed"] = master_seed
        rows.append(row)
        if index % 50 == 0 or index == len(jobs):
            print(f"completed {index}/{len(jobs)} independent chains")
    return pd.DataFrame(rows).sort_values(["lattice_size", "temperature", "chain"]).reset_index(drop=True)


def summarize_chains(chains: pd.DataFrame) -> pd.DataFrame:
    required = {
        "lattice_size", "temperature", "chain", "seed", "mean_abs_M",
        "n_samples", "acceptance_fraction", "data_kind", "model", "master_seed",
    }
    missing = required.difference(chains.columns)
    if missing:
        raise ValueError(f"missing chain columns: {sorted(missing)}")
    if chains.duplicated(["lattice_size", "temperature", "chain"]).any():
        raise ValueError("duplicate L/T/chain row")
    if chains["seed"].duplicated().any():
        raise ValueError("chain seeds must be globally unique")
    rows: list[dict[str, int | float | str]] = []
    tc = exact_tc()
    for (L, T), group in chains.groupby(["lattice_size", "temperature"], sort=True):
        master_seeds = group["master_seed"].unique()
        models = group["model"].unique()
        if len(master_seeds) != 1 or len(models) != 1:
            raise ValueError("each L/T group must have one master seed and one model")
        values = group["mean_abs_M"].to_numpy(float) / float(int(L) ** 2)
        m_inf = float(onsager_magnetization(float(T)))
        tau = (float(T) - tc) / tc
        rows.append(
            {
                "schema_version": 1,
                "lattice_size": int(L),
                "temperature": float(T),
                "n_chains": int(len(group)),
                "master_seed": int(master_seeds[0]),
                "model": str(models[0]),
                "magnetization_estimator": "mean_abs_M_over_L2",
                "m_L_mean": float(values.mean()),
                "m_L_sem": float(values.std(ddof=1) / np.sqrt(len(values))),
                "mean_acceptance_fraction": float(group["acceptance_fraction"].mean()),
                "m_infinity_exact": m_inf,
                "tau": tau,
                "fss_x_L_abs_tau_nu": float(int(L) * abs(tau) ** NU),
                "m_L_over_m_infinity": float(values.mean() / m_inf) if m_inf > 0 else np.nan,
                "data_kind": "synthetic_monte_carlo",
            }
        )
    return pd.DataFrame(rows)


def plot_reproduction(summary: pd.DataFrame, png_path: Path, pdf_path: Path, sampling_label: str) -> None:
    """Create an original two-panel rendering of the paper's scientific target."""
    colors = {10: "#D9A32C", 20: "#C45A2D", 40: "#2773B8"}
    markers = {10: "o", 20: "s", 40: "D"}
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 10.5,
            "axes.titleweight": "bold",
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.grid": True,
            "grid.alpha": 0.22,
            "grid.linewidth": 0.7,
        }
    )
    fig, (ax_a, ax_b) = plt.subplots(1, 2, figsize=(11.6, 5.15), constrained_layout=True)

    for L in sorted(summary["lattice_size"].unique()):
        part = summary.loc[summary["lattice_size"] == L].sort_values("temperature")
        ax_a.plot(
            part["temperature"], part["m_L_mean"], color=colors[int(L)], lw=1.7,
            marker=markers[int(L)], ms=3.4, markevery=2, label=f"Monte Carlo  L={int(L)}",
        )
        ax_a.fill_between(
            part["temperature"].to_numpy(float),
            (part["m_L_mean"] - part["m_L_sem"]).to_numpy(float),
            (part["m_L_mean"] + part["m_L_sem"]).to_numpy(float),
            color=colors[int(L)], alpha=0.16, linewidth=0,
        )

    dense_temperature = np.linspace(1.5, 3.0, 1200)
    ax_a.plot(dense_temperature, onsager_magnetization(dense_temperature), color="#202124", lw=2.0,
              label=r"Onsager $m_\infty(T)$ (exact)")
    ax_a.axvline(exact_tc(), color="#555555", lw=1.0, ls="--", alpha=0.8)
    ax_a.text(exact_tc() + 0.018, 0.045, rf"$T_c={exact_tc():.4f}$", rotation=90,
              va="bottom", ha="left", color="#444444", fontsize=9)
    ax_a.set(xlim=(1.5, 3.0), ylim=(0.0, 1.03), xlabel=r"Reduced temperature $T/J$",
             ylabel=r"Finite-size magnetization $m_L=\langle |M|\rangle/N$",
             title="(a) Finite-size magnetization versus Onsager limit")
    ax_a.legend(loc="lower left", frameon=True, framealpha=0.95, fontsize=9)

    below = summary.loc[(summary["temperature"] < exact_tc()) & summary["m_L_over_m_infinity"].notna()].copy()
    below = below.loc[below["fss_x_L_abs_tau_nu"] <= 3.5]
    for L in sorted(below["lattice_size"].unique()):
        part = below.loc[below["lattice_size"] == L].sort_values("fss_x_L_abs_tau_nu")
        ax_b.scatter(
            part["fss_x_L_abs_tau_nu"], part["m_L_over_m_infinity"],
            color=colors[int(L)], marker=markers[int(L)], s=28, edgecolor="white", linewidth=0.35,
            label=f"L={int(L)}", zorder=3,
        )
    ax_b.axhline(1.0, color="#202124", lw=1.3)
    ax_b.set(xlim=(0.0, 3.5), ylim=(0.96, 1.82), xlabel=r"Scaling variable $L|\tau|^\nu$  ($\nu=1$)",
             ylabel=r"$m_L/m_\infty$", title="(b) Finite-size-scaling collapse")
    # Panel (a) already maps every colour and marker to L; omitting a duplicate
    # legend keeps the inset and the near-critical points unobstructed.

    inset = ax_b.inset_axes([0.44, 0.45, 0.51, 0.47])
    for L in sorted(below["lattice_size"].unique()):
        part = below.loc[below["lattice_size"] == L].sort_values("fss_x_L_abs_tau_nu")
        inset.scatter(part["fss_x_L_abs_tau_nu"], part["m_L_over_m_infinity"],
                      color=colors[int(L)], marker=markers[int(L)], s=10, linewidth=0)
    inset.axhline(1.0, color="#202124", lw=0.8)
    inset.set_xscale("log")
    inset.set_xlim(0.025, 3.5)
    inset.set_ylim(0.96, 1.82)
    inset.set_xlabel(r"$L|\tau|^\nu$", fontsize=8)
    inset.set_ylabel(r"$m_L/m_\infty$", fontsize=8)
    inset.tick_params(labelsize=7.5)
    inset.grid(True, which="both", alpha=0.15)

    fig.suptitle("Independent method reproduction of Saratz et al. (2016), Figure 9(a-b)", fontsize=14, fontweight="bold")
    fig.text(
        0.5, -0.012,
        "New Monte Carlo data generated by this project; bands show SEM across independent chains.  " + sampling_label,
        ha="center", va="bottom", fontsize=8.6, color="#4A4A4A",
    )
    png_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(png_path, dpi=300, bbox_inches="tight", facecolor="white")
    fig.savefig(pdf_path, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def quantitative_checks(summary: pd.DataFrame) -> dict[str, object]:
    low = summary.loc[summary["temperature"] <= 2.0]
    tails = summary.loc[np.isclose(summary["temperature"], 3.0), ["lattice_size", "m_L_mean"]]
    tail_values = {str(int(row.lattice_size)): float(row.m_L_mean) for row in tails.itertuples()}
    finite_size_order = tail_values.get("10", np.nan) > tail_values.get("20", np.nan) > tail_values.get("40", np.nan)
    return {
        "mean_absolute_difference_from_onsager_for_T_le_2": float(
            np.mean(np.abs(low["m_L_mean"] - low["m_infinity_exact"]))
        ),
        "maximum_chain_sem": float(summary["m_L_sem"].max()),
        "m_L_at_T_3": tail_values,
        "expected_finite_size_order_at_T_3": "m_L(L=10) > m_L(L=20) > m_L(L=40)",
        "finite_size_order_at_T_3_pass": bool(finite_size_order),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--quick", action="store_true", help="run a separate non-scientific plumbing check")
    parser.add_argument("--output-root", type=Path, default=None)
    args = parser.parse_args()

    if not args.quick and not NUMBA_AVAILABLE:
        parser.error("the formal reproduction requires Numba; install requirements.txt first")

    if args.quick:
        sizes = (10, 20)
        temperatures = (1.5, 2.2, 2.26, 2.4, 3.0)
        chains = 2
        equilibration, measurement, interval = 40, 80, 4
        output_root = args.output_root or HERE / ".quick_results"
    else:
        sizes = SIZES
        temperatures = TEMPERATURES
        chains = CHAINS
        equilibration, measurement, interval = EQUILIBRATION_SWEEPS, MEASUREMENT_SWEEPS, SAMPLE_INTERVAL
        output_root = args.output_root or HERE / "results"

    output_root = output_root.resolve()
    try:
        output_root.relative_to(HERE.resolve())
    except ValueError as error:
        raise ValueError("--output-root must remain inside paper_reproduction/") from error

    reproduction_dir = output_root / "reproduction"
    figure_dir = output_root / "figures"
    reproduction_dir.mkdir(parents=True, exist_ok=True)
    figure_dir.mkdir(parents=True, exist_ok=True)
    chain_path = reproduction_dir / "figure9_chain_summary.csv"
    summary_path = reproduction_dir / "figure9_summary.csv"
    metadata_path = reproduction_dir / "figure9_metadata.json"
    png_path = figure_dir / "fig08_saratz_figure9ab_reproduction.png"
    pdf_path = figure_dir / "fig08_saratz_figure9ab_reproduction.pdf"

    started = time.perf_counter()
    chains_table = generate_chains(
        sizes, temperatures, chains, MASTER_SEED, equilibration, measurement, interval
    )
    summary = summarize_chains(chains_table)
    chains_table.to_csv(chain_path, index=False, float_format="%.12g")
    summary.to_csv(summary_path, index=False, float_format="%.12g")
    sampling_label = (
        f"This run: {chains} chains, {equilibration}+{measurement} sweeps/chain, "
        f"sample interval {interval}."
    )
    plot_reproduction(summary, png_path, pdf_path, sampling_label)
    elapsed = time.perf_counter() - started

    metadata = {
        "schema_version": 1,
        "reproduction_class": "independent_method_reproduction",
        "data_kind": "synthetic_monte_carlo",
        "paper": {
            "citation": "N. Saratz et al., Nature Communications 7, 13611 (2016)",
            "doi": PAPER_DOI,
            "url": PAPER_URL,
            "target": "Figure 9(a-b)",
            "reported_parameters_used": {
                "model": "unfrustrated square-lattice 2D Ising",
                "external_field": 0,
                "J": 1,
                "k_B": 1,
                "lattice_sizes": list(SIZES),
                "temperature_range_T_over_J": [1.5, 3.0],
            },
        },
        "tutorial_choices_not_recovered_from_paper": {
            "master_seed": MASTER_SEED,
            "chains_per_point": chains,
            "temperature_grid": list(temperatures),
            "equilibration_sweeps": equilibration,
            "measurement_sweeps": measurement,
            "sample_interval": interval,
            "stored_samples_per_chain": measurement // interval,
            "boundary_conditions": "periodic",
            "magnetization_estimator": "mean_abs_M_over_L2",
            "initial_state": "ordered_up",
            "update_algorithm": "red_black_metropolis",
            "rng_algorithm": "xorshift64star",
            "uncertainty": "SEM across independent chains; not autocorrelation-corrected",
        },
        "exact_reference": {"Tc": exact_tc(), "nu": NU, "magnetization": "Onsager spontaneous magnetization"},
        "software": {
            "python": sys.version.split()[0],
            "platform": platform.platform(),
            "numpy": np.__version__,
            "pandas": pd.__version__,
            "matplotlib": matplotlib.__version__,
            "numba_available": NUMBA_AVAILABLE,
            "numba": NUMBA_VERSION,
        },
        "quick_non_scientific_run": bool(args.quick),
        "rows": {"chains": len(chains_table), "summary": len(summary)},
        "elapsed_seconds": elapsed,
        "files": {
            "source_script": {"path": Path(__file__).relative_to(HERE).as_posix(), "sha256": sha256(Path(__file__))},
            "chain_csv": {"path": chain_path.relative_to(HERE).as_posix(), "sha256": sha256(chain_path)},
            "summary_csv": {"path": summary_path.relative_to(HERE).as_posix(), "sha256": sha256(summary_path)},
            "png": {"path": png_path.relative_to(HERE).as_posix(), "sha256": sha256(png_path)},
            "pdf": {"path": pdf_path.relative_to(HERE).as_posix(), "sha256": sha256(pdf_path)},
        },
        "quantitative_checks": quantitative_checks(summary),
        "limitations": [
            "The original Figure 9 numerical data and random seeds are not used.",
            "The tutorial sampling schedule is declared here rather than inferred from the published bitmap.",
            "SEM across chains is not an integrated-autocorrelation-time uncertainty.",
            "No hot/cold-start comparison, burn-in sensitivity study, or autocorrelation-time analysis was performed.",
            "Agreement in curve shape and finite-size ordering does not establish pointwise identity to the paper data.",
        ],
    }
    metadata_path.write_text(json.dumps(metadata, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {len(chains_table)} chain rows and {len(summary)} summary rows")
    print(f"figure: {png_path}")
    print(f"elapsed={elapsed:.2f} s; numba_available={NUMBA_AVAILABLE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
