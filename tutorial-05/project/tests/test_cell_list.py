import numpy as np
import pytest

from src.cell_list import counts_cell_list
from src.neighbors import counts_dense, counts_kdtree, generate_positions


def test_cell_list_periodic_faces_are_neighbors():
    xyz = [[0.2, 5, 5], [9.8, 5, 5], [5, 5, 5], [5.5, 5, 5]]
    np.testing.assert_array_equal(counts_cell_list(xyz, [10, 10, 10], 0.6), [1, 1, 1, 1])


def test_cell_list_matches_dense_reference():
    xyz, box = generate_positions(300, seed=101)
    np.testing.assert_array_equal(
        counts_cell_list(xyz, box, 3.0), counts_dense(xyz, box, 3.0)
    )


def test_cell_list_matches_kdtree_for_multiple_sizes():
    for n, seed in [(25, 5), (100, 13), (700, 29)]:
        xyz, box = generate_positions(n, seed=seed)
        np.testing.assert_array_equal(
            counts_cell_list(xyz, box, 3.0), counts_kdtree(xyz, box, 3.0)
        )


def test_cell_list_translation_by_box_vector():
    xyz, box = generate_positions(160, seed=73)
    shifted = xyz + np.array([box[0], -2 * box[1], 4 * box[2]])
    np.testing.assert_array_equal(
        counts_cell_list(shifted, box, 3.0), counts_cell_list(xyz, box, 3.0)
    )


def test_cell_list_permutation_equivariance():
    xyz, box = generate_positions(180, seed=44)
    permutation = np.random.default_rng(2026).permutation(len(xyz))
    original = counts_cell_list(xyz, box, 3.0)
    permuted = counts_cell_list(xyz[permutation], box, 3.0)
    np.testing.assert_array_equal(permuted, original[permutation])


def test_cell_list_duplicate_positions_and_cutoff_boundary():
    duplicate = [[1, 1, 1], [1, 1, 1]]
    np.testing.assert_array_equal(counts_cell_list(duplicate, [10, 10, 10], 1.0), [1, 1])
    boundary = [[1, 1, 1], [1.5, 1, 1]]
    np.testing.assert_array_equal(counts_cell_list(boundary, [10, 10, 10], 0.5), [1, 1])


def test_cell_list_empty_and_singleton():
    assert counts_cell_list(np.empty((0, 3)), [10, 10, 10], 1.0).size == 0
    np.testing.assert_array_equal(counts_cell_list([[1, 2, 3]], [10, 10, 10], 1.0), [0])


def test_cell_list_rejects_invalid_geometry_and_nonfinite_input():
    with pytest.raises(ValueError):
        counts_cell_list([[1, 1, 1]], [10, 10, 10], 5.0)
    with pytest.raises(ValueError):
        counts_cell_list([[0, np.nan, 0]], [10, 10, 10], 1.0)
