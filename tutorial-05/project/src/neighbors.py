"""Coordination numbers in a fully periodic orthorhombic simulation box.

The dense implementation is deliberately retained as a small-system reference.
The production implementation uses SciPy's periodic :class:`cKDTree` and stores
only the returned unordered neighbor pairs.

Limitations
-----------
* Orthorhombic boxes represented by three positive lengths.
* All three dimensions are periodic.
* One global cutoff satisfying ``0 < cutoff < min(box) / 2``.
* Every distinct atom is counted, including atoms at coincident coordinates.
"""
from __future__ import annotations

from numbers import Integral

import numpy as np
from scipy.spatial import cKDTree


def validate(positions, box, cutoff):
    """Validate and wrap an orthorhombic, fully periodic configuration."""
    xyz = np.asarray(positions, dtype=np.float64)
    lengths = np.asarray(box, dtype=np.float64)

    if xyz.ndim != 2 or xyz.shape[1] != 3:
        raise ValueError("positions must have shape (N, 3)")
    if lengths.shape != (3,) or not np.all(np.isfinite(lengths)):
        raise ValueError("box must contain three finite lengths")
    if np.any(lengths <= 0):
        raise ValueError("box lengths must be positive")
    if not np.all(np.isfinite(xyz)):
        raise ValueError("positions must be finite")

    cutoff_array = np.asarray(cutoff)
    if cutoff_array.ndim != 0:
        raise ValueError("cutoff must be a positive finite scalar")
    try:
        radius = float(cutoff_array)
    except (TypeError, ValueError) as exc:
        raise ValueError("cutoff must be a positive finite scalar") from exc
    if not np.isfinite(radius) or radius <= 0:
        raise ValueError("cutoff must be a positive finite scalar")
    if radius >= 0.5 * float(np.min(lengths)):
        raise ValueError("cutoff must satisfy 0 < cutoff < min(box) / 2")

    return np.mod(xyz, lengths), lengths, radius


def counts_dense(positions, box, cutoff):
    """Return coordination numbers using an intentional ``O(N^2)`` reference.

    This function is capped at 2,500 atoms because the broadcast displacement
    array has shape ``(N, N, 3)`` and is not suitable for production workloads.
    """
    xyz, lengths, radius = validate(positions, box, cutoff)
    n_atoms = len(xyz)
    if n_atoms == 0:
        return np.zeros(0, dtype=np.int64)
    if n_atoms > 2500:
        raise ValueError("dense reference capped at 2500 atoms to prevent OOM")

    delta = xyz[:, None, :] - xyz[None, :, :]
    delta -= lengths * np.rint(delta / lengths)
    dist2 = np.einsum("ijk,ijk->ij", delta, delta, optimize=True)
    within = dist2 <= radius**2
    np.fill_diagonal(within, False)
    return np.count_nonzero(within, axis=1).astype(np.int64, copy=False)


def counts_kdtree(positions, box, cutoff):
    """Return exact periodic coordination numbers using ``cKDTree``.

    The returned pair array requires ``O(E)`` storage for ``E`` unordered
    neighbor pairs. Tree construction and query cost depend on the spatial
    distribution and neighbor count; no blanket linear-time claim is made.
    """
    xyz, lengths, radius = validate(positions, box, cutoff)
    n_atoms = len(xyz)
    if n_atoms == 0:
        return np.zeros(0, dtype=np.int64)

    tree = cKDTree(xyz, boxsize=lengths)
    pairs = tree.query_pairs(radius, eps=0.0, output_type="ndarray")
    if pairs.size == 0:
        return np.zeros(n_atoms, dtype=np.int64)
    return np.bincount(pairs.ravel(), minlength=n_atoms).astype(np.int64)


def generate_positions(n, number_density=0.04, seed=20261116):
    """Generate deterministic uniform particles for benchmarks, not MD data."""
    if not isinstance(n, Integral) or isinstance(n, bool) or n < 0:
        raise ValueError("n must be a nonnegative integer")
    n = int(n)
    try:
        density = float(number_density)
    except (TypeError, ValueError) as exc:
        raise ValueError("number_density must be positive and finite") from exc
    if not np.isfinite(density) or density <= 0:
        raise ValueError("number_density must be positive and finite")

    if n == 0:
        lengths = np.full(3, 20.0, dtype=np.float64)
    else:
        lengths = np.full(3, (n / density) ** (1.0 / 3.0), dtype=np.float64)
    rng = np.random.default_rng(seed)
    return rng.random((n, 3), dtype=np.float64) * lengths, lengths

