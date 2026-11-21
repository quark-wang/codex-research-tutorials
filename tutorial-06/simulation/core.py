"""Deterministic Metropolis sampler for the periodic 2D Ising model."""
from __future__ import annotations

from dataclasses import asdict, dataclass

import numpy as np


@dataclass(frozen=True)
class ChainSummary:
    lattice_size: int
    temperature: float
    chain: int
    seed: int
    equilibration_sweeps: int
    measurement_sweeps: int
    sample_interval: int
    n_samples: int
    acceptance_fraction: float
    mean_E: float
    mean_E2: float
    mean_abs_M: float
    mean_M2: float
    mean_M4: float
    data_kind: str = "synthetic_monte_carlo"
    model: str = "2d_square_ising_zero_field"

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def exact_tc() -> float:
    """Onsager critical temperature in reduced units J/k_B."""
    return float(2.0 / np.log(1.0 + np.sqrt(2.0)))


def validate_spins(spins: np.ndarray) -> np.ndarray:
    lattice = np.asarray(spins)
    if lattice.ndim != 2 or lattice.shape[0] != lattice.shape[1] or lattice.shape[0] < 2:
        raise ValueError("spins must be a square 2D array with L >= 2")
    if not np.isin(lattice, (-1, 1)).all():
        raise ValueError("spins must contain only -1 and +1")
    return lattice


def total_energy(spins: np.ndarray) -> int:
    """Return H/J, counting right and down bonds once."""
    lattice = validate_spins(spins)
    bonds = np.sum(lattice * np.roll(lattice, -1, axis=0))
    bonds += np.sum(lattice * np.roll(lattice, -1, axis=1))
    return int(-bonds)


def magnetization(spins: np.ndarray) -> int:
    return int(validate_spins(spins).sum())


def local_delta_energy(spins: np.ndarray, row: int, column: int) -> int:
    """Return the exact H/J change for flipping one spin under periodic PBC."""
    lattice = validate_spins(spins)
    L = lattice.shape[0]
    i, j = int(row) % L, int(column) % L
    neighbor_sum = (
        lattice[(i - 1) % L, j]
        + lattice[(i + 1) % L, j]
        + lattice[i, (j - 1) % L]
        + lattice[i, (j + 1) % L]
    )
    return int(2 * lattice[i, j] * neighbor_sum)


def metropolis_sweep(
    spins: np.ndarray, beta: float, rng: np.random.Generator
) -> tuple[int, int]:
    """Perform one red-black Metropolis sweep; return accepted and attempted."""
    lattice = validate_spins(spins)
    if lattice.shape[0] < 4 or lattice.shape[0] % 2:
        raise ValueError("red-black periodic updates require an even lattice_size >= 4")
    if not np.isfinite(beta) or beta <= 0:
        raise ValueError("beta must be positive and finite")
    ii, jj = np.indices(lattice.shape)
    accepted = 0
    for parity in (0, 1):
        neighbors = (
            np.roll(lattice, 1, axis=0)
            + np.roll(lattice, -1, axis=0)
            + np.roll(lattice, 1, axis=1)
            + np.roll(lattice, -1, axis=1)
        )
        delta_E = 2 * lattice * neighbors
        mask = (ii + jj) % 2 == parity
        draw = rng.random(lattice.shape)
        # Evaluate the Boltzmann factor only for uphill moves.  Clipping the
        # downhill branch to zero avoids needless exponentials above one.
        uphill_probability = np.exp(-beta * np.maximum(delta_E, 0))
        flip = mask & ((delta_E <= 0) | (draw < uphill_probability))
        lattice[flip] *= -1
        accepted += int(flip.sum())
    return accepted, int(lattice.size)


def derive_job_seeds(master_seed: int, n_jobs: int) -> list[int]:
    if n_jobs <= 0:
        raise ValueError("n_jobs must be positive")
    children = np.random.SeedSequence(int(master_seed)).spawn(int(n_jobs))
    seeds = [int(child.generate_state(1, dtype=np.uint32)[0]) for child in children]
    if len(set(seeds)) != len(seeds):
        raise RuntimeError("unexpected seed collision")
    return seeds


def run_chain(
    lattice_size: int,
    temperature: float,
    chain: int,
    seed: int,
    equilibration_sweeps: int,
    measurement_sweeps: int,
    sample_interval: int,
) -> ChainSummary:
    """Run one independent chain and retain the moments needed downstream."""
    L, T = int(lattice_size), float(temperature)
    if L < 4 or L % 2:
        raise ValueError("lattice_size must be an even integer >= 4")
    if not np.isfinite(T) or T <= 0:
        raise ValueError("temperature must be positive and finite")
    if equilibration_sweeps < 0 or measurement_sweeps <= 0 or sample_interval <= 0:
        raise ValueError("invalid sweep counts or sample interval")
    rng = np.random.default_rng(int(seed))
    spins = rng.choice(np.array([-1, 1], dtype=np.int8), size=(L, L))
    beta = 1.0 / T
    accepted = attempted = 0
    for _ in range(int(equilibration_sweeps)):
        a, n = metropolis_sweep(spins, beta, rng)
        accepted += a
        attempted += n
    energies: list[float] = []
    moments: list[float] = []
    for sweep in range(1, int(measurement_sweeps) + 1):
        a, n = metropolis_sweep(spins, beta, rng)
        accepted += a
        attempted += n
        if sweep % int(sample_interval) == 0:
            energies.append(float(total_energy(spins)))
            moments.append(float(magnetization(spins)))
    if not energies:
        raise ValueError("no samples: measurement_sweeps < sample_interval")
    E = np.asarray(energies)
    M = np.asarray(moments)
    return ChainSummary(
        lattice_size=L,
        temperature=T,
        chain=int(chain),
        seed=int(seed),
        equilibration_sweeps=int(equilibration_sweeps),
        measurement_sweeps=int(measurement_sweeps),
        sample_interval=int(sample_interval),
        n_samples=int(len(E)),
        acceptance_fraction=float(accepted / attempted),
        mean_E=float(E.mean()),
        mean_E2=float(np.mean(E**2)),
        mean_abs_M=float(np.mean(np.abs(M))),
        mean_M2=float(np.mean(M**2)),
        mean_M4=float(np.mean(M**4)),
    )
