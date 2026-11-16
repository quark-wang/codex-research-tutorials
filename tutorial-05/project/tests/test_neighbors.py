import numpy as np
import pytest

from src.neighbors import counts_dense, counts_kdtree, generate_positions


def test_periodic_faces_are_neighbors():
    box = [10.0, 12.0, 14.0]
    xyz = [
        [0.2, 6, 7],
        [9.8, 6, 7],
        [5, 0.2, 7],
        [5, 11.8, 7],
        [5, 6, 0.2],
        [5, 6, 13.8],
    ]
    expected = [1, 1, 1, 1, 1, 1]
    np.testing.assert_array_equal(counts_kdtree(xyz, box, 0.6), expected)
    np.testing.assert_array_equal(counts_dense(xyz, box, 0.6), expected)


@pytest.mark.parametrize("n,seed", [(25, 1), (70, 17), (150, 31), (500, 48)])
def test_tree_exactly_agrees_with_dense(n, seed):
    xyz, box = generate_positions(n, seed=seed)
    np.testing.assert_array_equal(
        counts_kdtree(xyz, box, 3.0), counts_dense(xyz, box, 3.0)
    )


def test_translation_by_box_vector():
    box = np.array([18.0, 21.0, 27.0])
    xyz = np.random.default_rng(19).random((100, 3)) * box
    shifted = xyz + np.array([box[0], -2 * box[1], 3 * box[2]])
    np.testing.assert_array_equal(
        counts_kdtree(xyz, box, 3.0), counts_kdtree(shifted, box, 3.0)
    )


def test_permutation_equivariance():
    xyz, box = generate_positions(100, seed=11)
    permutation = np.random.default_rng(18).permutation(len(xyz))
    original = counts_kdtree(xyz, box, 3.0)
    permuted = counts_kdtree(xyz[permutation], box, 3.0)
    np.testing.assert_array_equal(permuted, original[permutation])


def test_empty_and_singleton():
    assert counts_kdtree(np.empty((0, 3)), [10, 10, 10], 1).size == 0
    np.testing.assert_array_equal(
        counts_kdtree([[1, 2, 3]], [10, 10, 10], 1), [0]
    )


def test_duplicate_positions_are_distinct_atoms():
    xyz = [[1, 1, 1], [1, 1, 1]]
    np.testing.assert_array_equal(counts_kdtree(xyz, [10, 10, 10], 1), [1, 1])


def test_at_cutoff_is_included():
    xyz = [[1, 1, 1], [1.5, 1, 1]]
    np.testing.assert_array_equal(counts_kdtree(xyz, [10, 10, 10], 0.5), [1, 1])


@pytest.mark.parametrize(
    "box,cutoff",
    [([10, 10, 10], 5), ([10, 10, 10], -1), ([0, 10, 10], 1), ([10, 10], 1)],
)
def test_invalid_geometry_rejected(box, cutoff):
    with pytest.raises(ValueError):
        counts_kdtree([[1, 1, 1]], box, cutoff)


def test_nonfinite_positions_rejected():
    with pytest.raises(ValueError):
        counts_kdtree([[0, np.nan, 0]], [10, 10, 10], 1)
    with pytest.raises(ValueError, match="scalar"):
        counts_kdtree([[0, 0, 0]], [10, 10, 10], [1, 2])


def test_atom_count_conservation():
    xyz, box = generate_positions(400, seed=6)
    counts = counts_kdtree(xyz, box, 3.0)
    assert int(counts.sum()) % 2 == 0
    assert len(counts) == len(xyz)
    assert counts.min() >= 0


def test_dense_safety_cap():
    xyz, box = generate_positions(2501)
    with pytest.raises(ValueError, match="capped"):
        counts_dense(xyz, box, 3.0)

