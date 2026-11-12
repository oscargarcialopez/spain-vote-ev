import numpy as np

from spain_vote_ev import power


def test_textbook_game():
    ss, bz = power.indices([2, 1, 1], quota=3)
    assert np.allclose(ss, [2 / 3, 1 / 6, 1 / 6])
    assert np.allclose(bz, [3 / 5, 1 / 5, 1 / 5])


def test_dummies_change_nothing():
    ss, bz = power.indices([2, 0, 1, 1, 0], quota=3)
    assert np.allclose(ss, [2 / 3, 0, 1 / 6, 1 / 6, 0])
    assert np.allclose(bz, [3 / 5, 0, 1 / 5, 1 / 5, 0])


def test_majority_holder_has_all_power():
    ss, bz = power.indices([180, 100, 70], quota=176)
    assert np.allclose(ss, [1, 0, 0]) and np.allclose(bz, [1, 0, 0])


def test_shapley_sums_to_one_on_2023_congress():
    seats = [137, 121, 33, 31, 7, 7, 6, 5, 1, 1, 1]
    ss, bz = power.indices(seats)
    assert np.isclose(ss.sum(), 1) and np.isclose(bz.sum(), 1)
    # brute force over all orders is too slow; check against coalition enumeration instead
    n = len(seats)
    swings = np.zeros(n)
    for mask in range(1 << n):
        w = sum(seats[j] for j in range(n) if mask >> j & 1)
        for i in range(n):
            if not mask >> i & 1 and w < 176 <= w + seats[i]:
                swings[i] += 1
    assert np.allclose(bz, swings / swings.sum())
