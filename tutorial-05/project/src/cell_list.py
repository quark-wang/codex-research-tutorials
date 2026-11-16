"""Teaching implementation of a periodic orthorhombic cell-linked list.

The implementation is intentionally written in Python for readability.  It
uses cells whose edge lengths are at least the cutoff, so examining the 27
adjacent cells is sufficient under the minimum-image convention.
"""
from __future__ import annotations

from itertools import product

import numpy as np

from .neighbors import validate


_OFFSETS = tuple(product((-1, 0, 1), repeat=3))


def counts_cell_list(positions, box, cutoff):
    """Return per-particle coordination numbers using a periodic cell list.

    This function has the same geometric contract as
    :func:`src.neighbors.counts_kdtree`: a fully periodic orthorhombic box,
    one global cutoff, no self pairs, and coincident distinct particles are
    counted as neighbors.
    """

    xyz, lengths, radius = validate(positions, box, cutoff)
    n_particles = len(xyz)
    if n_particles == 0:
        return np.zeros(0, dtype=np.int64)

    # floor(L / r) gives cell edges L / n_cells >= r.  validate() enforces
    # r < min(L)/2, so there are at least two cells per direction, but the
    # maximum keeps the implementation robust if that contract is relaxed.
    n_cells = np.maximum(np.floor(lengths / radius).astype(np.int64), 1)
    cell_width = lengths / n_cells
    cell_index = np.floor(xyz / cell_width).astype(np.int64) % n_cells

    cells: dict[tuple[int, int, int], list[int]] = {}
    for particle, key_array in enumerate(cell_index):
        key = tuple(int(value) for value in key_array)
        cells.setdefault(key, []).append(particle)

    counts = np.zeros(n_particles, dtype=np.int64)
    radius_squared = radius * radius

    for i in range(n_particles):
        home = cell_index[i]
        # With two cells along a dimension, offsets -1 and +1 wrap to the
        # same cell.  Deduplication prevents double counting in that case.
        neighbor_cells = {
            tuple(int(value) for value in ((home + offset) % n_cells))
            for offset in _OFFSETS
        }
        for key in neighbor_cells:
            for j in cells.get(key, ()):
                if j <= i:
                    continue
                displacement = xyz[j] - xyz[i]
                displacement -= lengths * np.rint(displacement / lengths)
                if float(np.dot(displacement, displacement)) <= radius_squared:
                    counts[i] += 1
                    counts[j] += 1

    return counts
