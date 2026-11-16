import json

import numpy as np
import pytest

from paper_reproduction.reproduce_figure3 import (
    DEFAULT_SIZES,
    R_MAX,
    box_length,
    generate_points,
    run_benchmark,
    scipy_query,
)


def test_box_length_and_points_are_deterministic():
    assert DEFAULT_SIZES == (50, 80, 100, 200, 400, 600, 1000, 2000, 3000, 5000)
    length = box_length(1200)
    expected = (4 * np.pi * 1200 / (3 * 12)) ** (1 / 3)
    assert length == pytest.approx(expected)
    length_a, points_a = generate_points(1200, seed=7)
    length_b, points_b = generate_points(1200, seed=7)
    assert length_a == pytest.approx(length_b)
    np.testing.assert_array_equal(points_a, points_b)
    assert np.all(points_a >= -length_a / 2)
    assert np.all(points_a < length_a / 2)


def test_scipy_query_is_periodic_directed_and_includes_self():
    length = 10.0
    points = np.array([
        [-4.9, 0.0, 0.0],
        [4.9, 0.0, 0.0],
        [0.0, 0.0, 0.0],
    ], dtype=np.float32)
    # Three self relations plus both directions for the pair across x boundary.
    assert R_MAX == 1.0
    assert scipy_query(length, points) == 5


def test_partial_run_writes_auditable_outputs(tmp_path):
    with pytest.raises(RuntimeError, match="freud-analysis is unavailable"):
        run_benchmark(tmp_path / "fail", sizes=[20], number=1, repeats=1,
                      freud_module=None, allow_partial=False)
    result = run_benchmark(tmp_path / "partial", sizes=[20], number=1, repeats=1,
                           freud_module=None, allow_partial=True,
                           freud_import_error="test: unavailable")
    assert result["complete"] is False
    assert result["csv"].is_file()
    assert result["png"].name == "figure3_partial_scipy_only.png"
    assert result["png"].is_file() and result["pdf"].is_file()
    metadata = json.loads(result["metadata"].read_text(encoding="utf-8"))
    assert metadata["status"] == "partial_scipy_only"
    assert metadata["freud_import_error"] == "test: unavailable"

