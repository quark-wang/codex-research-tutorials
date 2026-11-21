import numpy as np
import pandas as pd
import pytest

from analysis.observables import (
    binder_crossings,
    critical_summary,
    load_chain_table,
    per_chain_observables,
    summarize_observables,
    susceptibility_peak,
)


def fixture_frame():
    rows = []
    seed = 100
    for L in (8, 16):
        for T in (2.0, 2.2, 2.4):
            for chain in (0, 1):
                N = L * L
                mean_E = -1.5 * N
                mean_M = (0.8 if T == 2.0 else 0.45 if T == 2.2 else 0.2) * N
                rows.append({
                    "lattice_size": L, "temperature": T, "chain": chain,
                    "seed": seed, "n_samples": 100, "acceptance_fraction": 0.3,
                    "mean_E": mean_E, "mean_E2": mean_E**2 + 0.5 * N,
                    "mean_abs_M": mean_M, "mean_M2": mean_M**2 + 0.4 * N,
                    "mean_M4": 2.0 * (mean_M**2 + 0.4 * N) ** 2,
                    "data_kind": "synthetic_monte_carlo", "model": "2d_square_ising_zero_field",
                    "master_seed": 77,
                })
                seed += 1
    return pd.DataFrame(rows)


def test_per_chain_formulas_match_manual_values():
    frame = fixture_frame().iloc[[0]].copy()
    out = per_chain_observables(frame).iloc[0]
    N, beta = 64, 0.5
    assert out.energy_per_spin == pytest.approx(-1.5)
    assert out.abs_magnetization_per_spin == pytest.approx(0.8)
    assert out.heat_capacity_per_spin == pytest.approx(beta**2 * 0.5)
    assert out.susceptibility_abs_per_spin == pytest.approx(beta * 0.4)
    assert out.binder_u4 == pytest.approx(1 - 2 / 3)


def test_summary_reports_chain_sem_not_sample_sem():
    out = per_chain_observables(fixture_frame())
    summary = summarize_observables(out)
    assert set(summary.n_chains) == {2}
    assert (summary.filter(like="_sem") >= 0).all().all()


def test_summary_sem_uses_ddof_one_across_chains():
    frame = per_chain_observables(fixture_frame())
    mask = (frame.lattice_size == 8) & (frame.temperature == 2.0)
    frame.loc[mask, "energy_per_spin"] = [-1.0, -1.4]
    summary = summarize_observables(frame)
    row = summary.loc[(summary.lattice_size == 8) & (summary.temperature == 2.0)].iloc[0]
    expected = np.std([-1.0, -1.4], ddof=1) / np.sqrt(2)
    assert row.energy_per_spin_sem == pytest.approx(expected)


def test_row_order_does_not_change_summary():
    frame = fixture_frame()
    a = summarize_observables(per_chain_observables(frame))
    b = summarize_observables(per_chain_observables(frame.sample(frac=1, random_state=8)))
    pd.testing.assert_frame_equal(a, b)


def test_susceptibility_peak_interpolates_inside_grid():
    summary = pd.DataFrame({
        "lattice_size": [8, 8, 8, 16, 16, 16],
        "temperature": [2.0, 2.2, 2.4] * 2,
        "susceptibility_abs_per_spin_mean": [1, 2, 1, 1, 4, 2],
    })
    peak = susceptibility_peak(summary)
    assert peak["lattice_size"] == 16
    assert 2.0 < peak["temperature_estimate"] < 2.4


def test_binder_crossing_linear_interpolation():
    summary = pd.DataFrame({
        "lattice_size": [8, 8, 16, 16],
        "temperature": [2.1, 2.4, 2.1, 2.4],
        "binder_u4_mean": [0.65, 0.45, 0.60, 0.50],
    })
    crossings = binder_crossings(summary)
    assert len(crossings) == 1
    assert crossings[0]["temperature_estimate"] == pytest.approx(2.25)


def test_binder_crossing_does_not_extrapolate_without_sign_change():
    summary = pd.DataFrame({
        "lattice_size": [8, 8, 16, 16],
        "temperature": [2.1, 2.4, 2.1, 2.4],
        "binder_u4_mean": [0.65, 0.55, 0.60, 0.50],
    })
    assert binder_crossings(summary) == []


def test_critical_summary_keeps_exact_value_as_separate_reference():
    frame = fixture_frame()
    summary = summarize_observables(per_chain_observables(frame))
    out = critical_summary(summary)
    assert out["data_kind"] == "synthetic_monte_carlo"
    assert out["exact_tc_reduced"] == pytest.approx(2.269185314213022)


def test_loader_rejects_duplicate_job(tmp_path):
    frame = fixture_frame()
    frame = pd.concat([frame, frame.iloc[[0]]], ignore_index=True)
    path = tmp_path / "bad.csv"
    frame.to_csv(path, index=False)
    with pytest.raises(ValueError, match="duplicate"):
        load_chain_table(path)


def test_loader_rejects_duplicate_seed(tmp_path):
    frame = fixture_frame()
    frame.loc[1, "seed"] = frame.loc[0, "seed"]
    path = tmp_path / "bad.csv"
    frame.to_csv(path, index=False)
    with pytest.raises(ValueError, match="seeds"):
        load_chain_table(path)
