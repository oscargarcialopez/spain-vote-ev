"""Seat allocation in a constituency (LOREG art. 163) and how far each list is from one more seat.

Rules: lists below 3% of the constituency's valid votes (blank votes count as valid) take no
part; the seats go to the largest quotients votes/1, votes/2, ...; a tie between quotients goes
to the list with more votes, and an exact tie in votes is drawn by lot (art. 163.1.c-d). Ceuta
and Melilla elect one deputy each, which D'Hondt with one seat already is: the plurality winner.

`allocate_exact` applies the rules with exact fractions and is checked against every official
result since 2015 (tests). `allocate` is the vectorised version for simulated (continuous)
votes, where ties have probability zero.
"""

from __future__ import annotations

from fractions import Fraction

import numpy as np

THRESHOLD = 0.03


def allocate_exact(votes: list[int], seats: int, valid: int,
                   threshold: float = THRESHOLD) -> list[int]:
    """Seats per list with LOREG's tie rule (a draw by lot is replaced by list order)."""
    eligible = [v >= Fraction(threshold).limit_denominator() * valid for v in votes]
    quotients = [(Fraction(v, k), v, -i, i) for i, v in enumerate(votes) if eligible[i]
                 for k in range(1, seats + 1)]
    quotients.sort(reverse=True)
    out = [0] * len(votes)
    for _, _, _, i in quotients[:seats]:
        out[i] += 1
    return out


def allocate(votes: np.ndarray, seats: int, eligible: np.ndarray) -> np.ndarray:
    """votes (n, P) float, eligible (n, P) bool -> seats (n, P) int."""
    n, p = votes.shape
    if seats == 0:
        return np.zeros((n, p), dtype=np.int16)
    div = np.arange(1, seats + 1, dtype=float)
    q = np.where(eligible[:, :, None], votes[:, :, None] / div, -np.inf).reshape(n, p * seats)
    top = np.argpartition(-q, seats - 1, axis=1)[:, :seats] // seats  # list of each seat
    return (top[:, :, None] == np.arange(p)).sum(axis=1).astype(np.int16)


def margins(votes: np.ndarray, seats: np.ndarray, present: np.ndarray, valid: np.ndarray,
            threshold: float = THRESHOLD) -> tuple[np.ndarray, np.ndarray]:
    """For each list, the extra votes it needs to win one more seat (Δ, inf if it cannot),
    and the list that would lose that seat.

    A list gains a seat when its next quotient, votes/(seats+1), passes the smallest quotient
    that another list is winning with; that list loses the seat. A list below the threshold
    must also reach 3% of the valid votes (which grow with its own extra votes)."""
    n, p = votes.shape
    with np.errstate(divide="ignore", invalid="ignore"):
        last = np.where(seats > 0, votes / np.maximum(seats, 1), np.inf)
    order = np.argsort(last, axis=1)[:, :2]
    a1, a2 = order[:, 0], order[:, 1]
    m1 = last[np.arange(n), a1]
    m2 = last[np.arange(n), a2]
    is_min = np.arange(p)[None, :] == a1[:, None]
    q_other = np.where(is_min, m2[:, None], m1[:, None])
    loser = np.where(is_min, a2[:, None], a1[:, None])
    need = q_other * (seats + 1) - votes
    below = votes < threshold * valid[:, None]
    need_thr = (threshold * valid[:, None] - votes) / (1 - threshold)
    need = np.where(below, np.maximum(need, need_thr), need)
    need = np.where(present, need, np.inf)
    return need, loser
