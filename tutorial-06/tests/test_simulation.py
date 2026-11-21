import numpy as np
import pytest

from simulation.core import (
    derive_job_seeds,
    exact_tc,
    local_delta_energy,
    magnetization,
    metropolis_sweep,
    run_chain,
    total_energy,
    validate_spins,
)


def test_all_up_ground_state_energy_and_magnetization():
    spins = np.ones((4, 4), dtype=np.int8)
    assert total_energy(spins) == -2 * spins.size
    assert magnetization(spins) == spins.size


def test_single_flip_costs_eight_j():
    spins = np.ones((4, 4), dtype=np.int8)
    e0 = total_energy(spins)
    spins[0, 0] = -1
    assert total_energy(spins) - e0 == 8


def test_local_delta_matches_direct_energy_difference_and_allowed_values():
    rng = np.random.default_rng(20261121)
    spins = rng.choice([-1, 1], size=(8, 8)).astype(np.int8)
    observed = set()
    for i in range(8):
        for j in range(8):
            delta = local_delta_energy(spins, i, j)
            trial = spins.copy()
            trial[i, j] *= -1
            assert delta == total_energy(trial) - total_energy(spins)
            observed.add(delta)
    assert observed.issubset({-8, -4, 0, 4, 8})


def test_energy_is_invariant_under_periodic_translation():
    rng = np.random.default_rng(8)
    spins = rng.choice([-1, 1], size=(8, 8)).astype(np.int8)
    shifted = np.roll(np.roll(spins, 3, axis=0), -2, axis=1)
    assert total_energy(shifted) == total_energy(spins)


def test_periodic_stripe_energy_is_known():
    spins = np.ones((4, 4), dtype=np.int8)
    spins[:, 2:] = -1
    assert total_energy(spins) == -16


def test_spin_validation_rejects_invalid_inputs():
    with pytest.raises(ValueError):
        validate_spins(np.zeros((4, 4)))
    with pytest.raises(ValueError):
        validate_spins(np.ones((3, 4)))


def test_sweep_preserves_spin_alphabet_and_attempt_count():
    rng = np.random.default_rng(7)
    spins = rng.choice([-1, 1], size=(8, 8)).astype(np.int8)
    accepted, attempted = metropolis_sweep(spins, 1 / 2.3, rng)
    assert attempted == 64
    assert 0 <= accepted <= attempted
    assert set(np.unique(spins)).issubset({-1, 1})


def test_sweep_rejects_odd_periodic_lattice():
    spins = np.ones((5, 5), dtype=np.int8)
    with pytest.raises(ValueError, match="even"):
        metropolis_sweep(spins, 1 / 2.3, np.random.default_rng(1))


def test_sweep_is_reproducible_with_local_rng():
    initial = np.where(np.indices((8, 8)).sum(axis=0) % 3, 1, -1).astype(np.int8)
    a, b = initial.copy(), initial.copy()
    out_a = metropolis_sweep(a, 1 / 2.2, np.random.default_rng(99))
    out_b = metropolis_sweep(b, 1 / 2.2, np.random.default_rng(99))
    np.testing.assert_array_equal(a, b)
    assert out_a == out_b


def test_job_seeds_are_distinct_and_reproducible():
    assert derive_job_seeds(123, 10) == derive_job_seeds(123, 10)
    assert len(set(derive_job_seeds(123, 10))) == 10


def test_chain_summary_is_reproducible_and_bounded():
    kwargs = dict(lattice_size=8, temperature=2.3, chain=0, seed=17,
                  equilibration_sweeps=20, measurement_sweeps=40, sample_interval=4)
    first, second = run_chain(**kwargs), run_chain(**kwargs)
    assert first == second
    assert first.n_samples == 10
    assert -2 <= first.mean_E / 64 <= 2
    assert 0 <= first.mean_abs_M / 64 <= 1
    assert 0 <= first.acceptance_fraction <= 1


def test_low_temperature_is_more_ordered_than_high_temperature():
    low = run_chain(8, 1.5, 0, 11, 200, 400, 4)
    high = run_chain(8, 4.0, 0, 12, 200, 400, 4)
    assert low.mean_abs_M / 64 > high.mean_abs_M / 64


def test_exact_tc_reference():
    assert exact_tc() == pytest.approx(2.269185314213022, abs=1e-12)


@pytest.mark.parametrize("kwargs", [
    {"lattice_size": 5, "temperature": 2.0},
    {"lattice_size": 8, "temperature": 0.0},
])
def test_invalid_chain_geometry(kwargs):
    base = dict(lattice_size=8, temperature=2.0, chain=0, seed=1,
                equilibration_sweeps=1, measurement_sweeps=4, sample_interval=2)
    base.update(kwargs)
    with pytest.raises(ValueError):
        run_chain(**base)
