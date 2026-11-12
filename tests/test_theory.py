import numpy as np

from spain_vote_ev import theory


def test_break_even_points_cover_the_cost():
    p, n = 1e-7, 50_000_000
    b = np.array([10.0, 100.0, 1000.0])
    alpha = theory.break_even_alpha(p, n, b)
    assert np.allclose(p * n * b * alpha, theory.COST)
    assert np.isclose(p * theory.break_even_benefit(p), theory.COST)


def test_influence_break_even_pays_the_hour():
    p = 1e-7
    for v in theory.VOTES_PER_HOUR:
        b = theory.influence(p, v)["break_even_benefit"]
        assert np.isclose(v * p * b, theory.VALUE_OF_TIME)
