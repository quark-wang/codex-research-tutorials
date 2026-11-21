from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from paper_reproduction.run_figure9_reproduction import (
    TEMPERATURES,
    derive_seeds,
    exact_tc,
    onsager_magnetization,
    run_chain,
    summarize_chains,
)


def test_exact_onsager_reference() -> None:
    tc = exact_tc()
    values = onsager_magnetization(np.array([1.5, tc, 3.0]))
    assert tc == pytest.approx(2.269185314213022)
    assert 0.98 < values[0] < 1.0
    assert values[1] == 0.0
    assert values[2] == 0.0


def test_declared_temperature_grid_covers_paper_range_and_resolves_tc() -> None:
    assert TEMPERATURES[0] == 1.5
    assert TEMPERATURES[-1] == 3.0
    near = [value for value in TEMPERATURES if 2.20 <= value <= 2.32]
    assert max(np.diff(near)) == pytest.approx(0.01)


def test_seed_derivation_is_distinct_and_repeatable() -> None:
    first = derive_seeds(20261121, 8)
    second = derive_seeds(20261121, 8)
    assert first == second
    assert len(set(first)) == 8


def test_small_chain_is_deterministic_and_records_sampling() -> None:
    first = run_chain(4, 2.2, 12345, 4, 12, 3)
    second = run_chain(4, 2.2, 12345, 4, 12, 3)
    assert first == second
    assert first["n_samples"] == 4
    assert 0 <= first["mean_abs_M"] <= 16
    assert 0 <= first["acceptance_fraction"] <= 1


def test_odd_periodic_lattice_is_rejected() -> None:
    with pytest.raises(ValueError, match="even lattice"):
        run_chain(5, 2.2, 123, 4, 12, 3)


def test_summary_uses_chain_sem_and_exact_reference() -> None:
    rows = []
    for chain, mean_abs_m in enumerate((80.0, 84.0)):
        rows.append(
            {
                "lattice_size": 10,
                "temperature": 2.0,
                "chain": chain,
                "seed": 10 + chain,
                "mean_abs_M": mean_abs_m,
                "n_samples": 10,
                "acceptance_fraction": 0.2,
                "data_kind": "synthetic_monte_carlo",
                "model": "2d_square_ising_zero_field",
                "master_seed": 20261121,
            }
        )
    summary = summarize_chains(pd.DataFrame(rows))
    assert summary.loc[0, "m_L_mean"] == pytest.approx(0.82)
    assert summary.loc[0, "m_L_sem"] == pytest.approx(0.02)
    assert summary.loc[0, "m_infinity_exact"] > 0
    assert np.isfinite(summary.loc[0, "m_L_over_m_infinity"])
    assert summary.loc[0, "master_seed"] == 20261121
    assert summary.loc[0, "magnetization_estimator"] == "mean_abs_M_over_L2"


def test_fss_variable_is_L_times_abs_tau_to_nu() -> None:
    rows = []
    for chain in range(2):
        rows.append(
            {
                "lattice_size": 20,
                "temperature": 2.0,
                "chain": chain,
                "seed": 100 + chain,
                "mean_abs_M": 360.0 + chain,
                "n_samples": 10,
                "acceptance_fraction": 0.2,
                "data_kind": "synthetic_monte_carlo",
                "model": "2d_square_ising_zero_field",
                "master_seed": 20261121,
            }
        )
    summary = summarize_chains(pd.DataFrame(rows))
    expected_tau = (2.0 - exact_tc()) / exact_tc()
    assert summary.loc[0, "fss_x_L_abs_tau_nu"] == pytest.approx(20 * abs(expected_tau))


def test_ratio_is_nan_at_and_above_tc() -> None:
    rows = []
    for temperature_index, temperature in enumerate((exact_tc(), 3.0)):
        for chain in range(2):
            rows.append(
                {
                    "lattice_size": 10,
                    "temperature": temperature,
                    "chain": chain,
                    "seed": 1000 + 10 * temperature_index + chain,
                    "mean_abs_M": 10.0,
                    "n_samples": 10,
                    "acceptance_fraction": 0.5,
                    "data_kind": "synthetic_monte_carlo",
                    "model": "2d_square_ising_zero_field",
                    "master_seed": 20261121,
                }
            )
    summary = summarize_chains(pd.DataFrame(rows))
    assert summary["m_L_over_m_infinity"].isna().all()
