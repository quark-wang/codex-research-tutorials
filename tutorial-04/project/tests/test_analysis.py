import numpy as np
import pytest
from src.analysis import arrhenius_fit, KB_EV_PER_K


def test_known_activation_energy():
    t = np.array([700, 800, 900, 1000, 1100, 1200], dtype=float)
    d = 2e-6 * np.exp(-0.42 / (KB_EV_PER_K * t))
    got = arrhenius_fit(t, d)
    assert got['Ea_eV'] == pytest.approx(0.42, rel=1e-10)
    assert got['D0_m2_s'] == pytest.approx(2e-6, rel=1e-10)


def test_unit_invariance():
    t = np.array([750, 850, 950, 1050, 1150], dtype=float)
    d = 1e-6 * np.exp(-0.36 / (KB_EV_PER_K * t))
    assert arrhenius_fit(t, d)['Ea_eV'] == pytest.approx(arrhenius_fit(t, d*1e4)['Ea_eV'])


@pytest.mark.parametrize('bad', [[1e-9, 0, 2e-9], [1e-9, -2e-9, 2e-9], [1e-9, np.nan, 2e-9]])
def test_reject_invalid_D(bad):
    with pytest.raises(ValueError):
        arrhenius_fit([800, 900, 1000], bad)


def test_weighting_matches_numpy():
    t = np.array([700, 800, 900, 1000, 1100], dtype=float)
    d = 2e-6 * np.exp(-0.42 / (KB_EV_PER_K*t)) * np.array([1, 1, 1.3, 1, 1])
    sem = d * np.array([.02, .02, .5, .02, .02])
    slope, _ = np.polyfit(1000/t, np.log(d), 1, w=d/sem)
    result = arrhenius_fit(t, d, sem)
    assert result['slope'] == pytest.approx(slope)
