"""A priori voting power in the Congreso: Shapley-Shubik and Banzhaf indices of the weighted
majority game [176; seats of each list].

Both count how often a list is decisive, assuming any coalition can form: Shapley-Shubik over
the orders in which lists could join (the share of orders in which a list's seats take the
coalition past 176), Banzhaf over coalitions (how many losing coalitions it turns into winning
ones, normalised to sum to one). They measure arithmetic leverage, not who will govern.

Computed exactly by counting coalitions by size and seats (a generating-function table), with
each list removed from the table in turn.
"""

from __future__ import annotations

from math import factorial

import numpy as np

QUOTA = 176


def _table(weights: list[int]) -> np.ndarray:
    """C[k, w]: the number of coalitions of k lists with w seats."""
    total = sum(weights)
    c = np.zeros((len(weights) + 1, total + 1))
    c[0, 0] = 1
    for w in weights:
        shifted = np.zeros_like(c)
        shifted[1:, w:] = c[:-1, :total + 1 - w]
        c += shifted
    return c


def indices(weights: list[int], quota: int = QUOTA) -> tuple[np.ndarray, np.ndarray]:
    """(Shapley-Shubik, normalised Banzhaf) for each weight; zero weights get zero."""
    all_w = [int(w) for w in weights]
    keep = [i for i, w in enumerate(all_w) if w > 0]
    ss_all, bz_all = np.zeros(len(all_w)), np.zeros(len(all_w))
    if not keep:
        return ss_all, bz_all
    ss_k, bz_k = _indices([all_w[i] for i in keep], quota)
    ss_all[keep], bz_all[keep] = ss_k, bz_k
    return ss_all, bz_all


def _indices(weights: list[int], quota: int) -> tuple[np.ndarray, np.ndarray]:
    n = len(weights)
    full = _table(weights)
    total = sum(weights)
    ss, bz = np.zeros(n), np.zeros(n)
    coef = np.array([factorial(k) * factorial(n - k - 1) / factorial(n) for k in range(n)])
    for i, w in enumerate(weights):
        # the table without list i: D[k] = C[k] - D[k-1] shifted by w
        d = np.zeros_like(full)
        d[0] = full[0]
        for k in range(1, n + 1):
            d[k] = full[k].copy()
            d[k, w:] -= d[k - 1, :total + 1 - w]
        lo, hi = max(quota - w, 0), quota  # coalitions it turns from losing to winning
        swings = d[:n, lo:hi].sum(axis=1)
        ss[i] = float(swings @ coef)
        bz[i] = float(swings.sum())
    return ss, bz / bz.sum() if bz.sum() else bz


def over_simulations(seats: np.ndarray, sample: int = 10_000, seed: int = 7
                     ) -> tuple[np.ndarray, np.ndarray, int]:
    """Mean indices over a random sample of simulated parliaments (n, F)."""
    rng = np.random.default_rng(seed)
    rows = rng.choice(len(seats), size=min(sample, len(seats)), replace=False)
    cache: dict[tuple, tuple[np.ndarray, np.ndarray]] = {}
    ss_sum = np.zeros(seats.shape[1])
    bz_sum = np.zeros(seats.shape[1])
    for r in rows:
        key = tuple(int(x) for x in seats[r])
        if key not in cache:
            cache[key] = indices(list(key))
        ss, bz = cache[key]
        ss_sum += ss
        bz_sum += bz
    return ss_sum / len(rows), bz_sum / len(rows), len(rows)
