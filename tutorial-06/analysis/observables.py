"""Thermodynamic observables and transparent finite-size Tc estimators."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from simulation.core import exact_tc


REQUIRED = {
    "lattice_size", "temperature", "chain", "seed", "n_samples",
    "acceptance_fraction", "mean_E", "mean_E2", "mean_abs_M",
    "mean_M2", "mean_M4", "data_kind", "model", "master_seed",
}


def load_chain_table(path: str | Path) -> pd.DataFrame:
    frame = pd.read_csv(path)
    missing = REQUIRED.difference(frame.columns)
    if missing:
        raise ValueError(f"missing columns: {sorted(missing)}")
    if frame.empty:
        raise ValueError("chain table is empty")
    numeric = sorted(REQUIRED.difference({"data_kind", "model"}))
    if not np.isfinite(frame[numeric]).all().all():
        raise ValueError("chain table contains non-finite numeric values")
    if set(frame["data_kind"]) != {"synthetic_monte_carlo"}:
        raise ValueError("unexpected data_kind")
    if set(frame["model"]) != {"2d_square_ising_zero_field"}:
        raise ValueError("unexpected model")
    if frame.duplicated(["lattice_size", "temperature", "chain"]).any():
        raise ValueError("duplicate L/T/chain rows")
    if frame["seed"].duplicated().any():
        raise ValueError("job seeds must be globally unique")
    counts = frame.groupby(["lattice_size", "temperature"])["chain"].nunique()
    if counts.nunique() != 1 or int(counts.iloc[0]) < 2:
        raise ValueError("every L/T group needs the same number of >=2 chains")
    if not frame["acceptance_fraction"].between(0, 1).all():
        raise ValueError("acceptance fraction outside [0,1]")
    return frame.sort_values(["lattice_size", "temperature", "chain"]).reset_index(drop=True)


def per_chain_observables(frame: pd.DataFrame) -> pd.DataFrame:
    """Transform stored moments into nonlinear observables per chain."""
    f = frame.copy()
    N = f["lattice_size"].astype(float) ** 2
    beta = 1.0 / f["temperature"].astype(float)
    f["energy_per_spin"] = f["mean_E"] / N
    f["abs_magnetization_per_spin"] = f["mean_abs_M"] / N
    var_E = np.maximum(0.0, f["mean_E2"] - f["mean_E"] ** 2)
    var_M_abs = np.maximum(0.0, f["mean_M2"] - f["mean_abs_M"] ** 2)
    f["heat_capacity_per_spin"] = beta**2 * var_E / N
    f["susceptibility_abs_per_spin"] = beta * var_M_abs / N
    denominator = 3.0 * f["mean_M2"] ** 2
    if (denominator <= 0).any():
        raise ValueError("Binder cumulant denominator must be positive")
    f["binder_u4"] = 1.0 - f["mean_M4"] / denominator
    return f


def summarize_observables(chain_observables: pd.DataFrame) -> pd.DataFrame:
    metrics = [
        "energy_per_spin", "abs_magnetization_per_spin",
        "heat_capacity_per_spin", "susceptibility_abs_per_spin",
        "binder_u4", "acceptance_fraction",
    ]
    rows: list[dict[str, object]] = []
    for (L, T), group in chain_observables.groupby(["lattice_size", "temperature"], sort=True):
        row: dict[str, object] = {
            "lattice_size": int(L), "temperature": float(T),
            "n_chains": int(len(group)), "data_kind": "synthetic_monte_carlo",
        }
        for metric in metrics:
            values = group[metric].to_numpy(float)
            row[f"{metric}_mean"] = float(values.mean())
            row[f"{metric}_sem"] = float(values.std(ddof=1) / np.sqrt(len(values)))
        rows.append(row)
    return pd.DataFrame(rows)


def susceptibility_peak(summary: pd.DataFrame) -> dict[str, float | int | str]:
    """Quadratic interpolation around the largest-size discrete chi peak."""
    L = int(summary["lattice_size"].max())
    sub = summary.loc[summary["lattice_size"] == L].sort_values("temperature").reset_index(drop=True)
    y = sub["susceptibility_abs_per_spin_mean"].to_numpy(float)
    x = sub["temperature"].to_numpy(float)
    i = int(np.argmax(y))
    estimate = float(x[i])
    method = "discrete_peak"
    if 0 < i < len(x) - 1:
        coeff = np.polyfit(x[i - 1:i + 2], y[i - 1:i + 2], 2)
        vertex = float(-coeff[1] / (2 * coeff[0])) if coeff[0] < 0 else np.nan
        if np.isfinite(vertex) and x[i - 1] <= vertex <= x[i + 1]:
            estimate, method = vertex, "local_quadratic_peak"
    return {
        "lattice_size": L,
        "temperature_estimate": estimate,
        "discrete_peak_temperature": float(x[i]),
        "peak_value": float(y[i]),
        "method": method,
    }


def binder_crossings(
    summary: pd.DataFrame, window: tuple[float, float] = (2.05, 2.50)
) -> list[dict[str, float | int]]:
    """Linearly interpolate adjacent-size U4 sign changes in a declared window."""
    sizes = sorted(int(v) for v in summary["lattice_size"].unique())
    results: list[dict[str, float | int]] = []
    for low, high in zip(sizes[:-1], sizes[1:]):
        a = summary.loc[summary["lattice_size"] == low, ["temperature", "binder_u4_mean"]]
        b = summary.loc[summary["lattice_size"] == high, ["temperature", "binder_u4_mean"]]
        merged = a.merge(b, on="temperature", suffixes=("_low", "_high")).sort_values("temperature")
        merged = merged.loc[merged["temperature"].between(*window)].reset_index(drop=True)
        diff = (merged["binder_u4_mean_low"] - merged["binder_u4_mean_high"]).to_numpy(float)
        temp = merged["temperature"].to_numpy(float)
        candidates: list[float] = []
        for i in range(len(temp) - 1):
            if diff[i] == 0:
                candidates.append(float(temp[i]))
            elif diff[i] * diff[i + 1] < 0:
                fraction = -diff[i] / (diff[i + 1] - diff[i])
                candidates.append(float(temp[i] + fraction * (temp[i + 1] - temp[i])))
        if candidates:
            # If noise causes more than one crossing, use the median without exact-Tc fitting.
            estimate = float(np.median(candidates))
            results.append({"L_low": low, "L_high": high, "temperature_estimate": estimate, "n_sign_changes": len(candidates)})
    return results


def critical_summary(summary: pd.DataFrame) -> dict[str, object]:
    peak = susceptibility_peak(summary)
    crossings = binder_crossings(summary)
    median_crossing = float(np.median([c["temperature_estimate"] for c in crossings])) if crossings else None
    exact = exact_tc()
    return {
        "schema_version": 1,
        "data_kind": "synthetic_monte_carlo",
        "model": "2d_square_ising_zero_field",
        "exact_tc_reduced": exact,
        "susceptibility_peak": peak,
        "binder_crossings": crossings,
        "binder_median_temperature": median_crossing,
        "binder_absolute_error": abs(median_crossing - exact) if median_crossing is not None else None,
        "limitations": [
            "finite sizes and discrete temperature grid",
            "SEM is across independent chains; no integrated-autocorrelation correction",
            "Metropolis equilibration is workload-specific, not a universal production guarantee",
        ],
    }


def write_analysis(chain_path: str | Path, result_dir: str | Path) -> dict[str, object]:
    target = Path(result_dir)
    target.mkdir(parents=True, exist_ok=True)
    chains = per_chain_observables(load_chain_table(chain_path))
    summary = summarize_observables(chains)
    critical = critical_summary(summary)
    chains.to_csv(target / "chain_observables.csv", index=False, float_format="%.12g")
    summary.to_csv(target / "thermodynamic_summary.csv", index=False, float_format="%.12g")
    (target / "critical_summary.json").write_text(json.dumps(critical, indent=2) + "\n", encoding="utf-8")
    return critical
