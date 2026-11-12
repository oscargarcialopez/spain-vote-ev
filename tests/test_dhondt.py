import numpy as np
import pandas as pd
import pytest

from spain_vote_ev import dhondt
from spain_vote_ev.sources import PROCESSED


def test_textbook_example():
    # 7 seats, 3% threshold: the classic example from the Ley Electoral's own illustration.
    votes = [168000, 104000, 72000, 64000, 40000, 32000]
    assert dhondt.allocate_exact(votes, 7, sum(votes)) == [3, 2, 1, 1, 0, 0]


def test_threshold_excludes_small_list():
    votes = [600, 300, 25]  # the last has 2.7% of 925 valid votes
    assert dhondt.allocate_exact(votes, 30, 925)[2] == 0
    assert dhondt.allocate_exact(votes, 30, 925)[0] + dhondt.allocate_exact(votes, 30, 925)[1] == 30


def test_tie_goes_to_more_votes():
    # quotients 300/2 = 150/1: the seat goes to the list with more votes
    assert dhondt.allocate_exact([300, 150], 2, 450) == [2, 0]


@pytest.mark.skipif(not (PROCESSED / "results.csv").exists(), reason="run voteev prepare")
def test_official_seats_reproduced():
    res = pd.read_csv(PROCESSED / "results.csv", dtype={"code": str})
    summ = pd.read_csv(PROCESSED / "summary.csv", dtype={"code": str}).set_index(
        ["election", "code"])
    for (e, code), g in res[res["label"] != "OTH"].groupby(["election", "code"]):
        seats = int(res[(res.election == e) & (res.code == code)]["seats"].sum())
        got = dhondt.allocate_exact(list(g["votes"]), seats, int(summ.loc[(e, code), "valid"]))
        assert got == list(g["seats"]), (e, code)


def test_vectorised_matches_exact():
    rng = np.random.default_rng(1)
    for _ in range(200):
        p, m = rng.integers(2, 9), rng.integers(1, 15)
        v = rng.integers(1, 100000, size=p)
        valid = int(v.sum() + rng.integers(0, 5000))
        exact = dhondt.allocate_exact(list(v), m, valid)
        elig = v >= 0.03 * valid
        fast = dhondt.allocate(v[None].astype(float) + rng.random(p) * 1e-6, m, elig[None])[0]
        assert list(fast) == exact


def test_margins_are_exact():
    rng = np.random.default_rng(2)
    for _ in range(300):
        p, m = rng.integers(2, 8), rng.integers(1, 12)
        v = rng.random(p) * 1e5
        valid = v.sum() * 1.01
        elig = v >= 0.03 * valid
        s = dhondt.allocate(v[None], m, elig[None])
        need, loser = dhondt.margins(v[None], s, np.ones((1, p), bool), np.array([valid]))
        for j in range(p):
            if not np.isfinite(need[0, j]):
                continue
            for eps, gain in ((-1e-3, 0), (1e-3, 1)):
                w = v.copy()
                w[j] += need[0, j] + eps
                val = valid + need[0, j] + eps
                s2 = dhondt.allocate(w[None], m, (w >= 0.03 * val)[None])
                assert s2[0, j] - s[0, j] == gain
                if gain:
                    assert s[0, loser[0, j]] - s2[0, loser[0, j]] == 1
