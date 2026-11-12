"""Why vote: the calculus of voting and what the probabilities imply.

Riker and Ordeshook (1968): a citizen votes when R = p·B − C + D > 0, with p the probability
that their vote decides the outcome, B the value they place on that outcome, C the cost of
voting and D any value of voting itself. Downs (1957) had noted that p is tiny, so p·B rarely
covers C. Edlin, Gelman and Kaplan (2007): if B counts the effect on everyone, B = N·b·α
(N people, an average benefit b each, weighted by α, how much the voter cares about another
person relative to themself), then p·B stays the same order however large N is, since p falls
roughly like 1/N while B grows like N.

Here C is time: MINUTES at VALUE_OF_TIME €/h. Influence (getting others to vote) is worth
votes moved per hour × p × B per hour, set against VALUE_OF_TIME. Persuading people to change
their vote is taken as zero (Kalla and Broockman, 2018); the votes moved per hour by turnout
canvassing are an assumption, given as a range, from US field experiments, not a Spanish
estimate.
"""

from __future__ import annotations

import numpy as np

VALUE_OF_TIME = 10.0          # €/h
MINUTES = 30                  # to go to the polling station, queue, vote and come back
COST = VALUE_OF_TIME * MINUTES / 60   # € per vote
VOTES_PER_HOUR = (0.1, 1.0)   # extra voters per hour of canvassing: assumption, US-based
B_GRID = np.logspace(0, 5, 101)        # € per person, for the social curve
ALPHA_GRID = np.logspace(-5, 0, 101)


def break_even_benefit(p: float, cost: float = COST) -> float:
    """B at which p·B = C."""
    return cost / p


def break_even_alpha(p: float, n_people: int, b: np.ndarray, cost: float = COST) -> np.ndarray:
    """α at which p·N·b·α = C."""
    return cost / (p * n_people * b)


def influence(p: float, votes_per_hour: float, value_of_time: float = VALUE_OF_TIME) -> dict:
    """The benefit B at which an hour spent getting others to vote is worth its time."""
    return {"votes_per_hour": votes_per_hour,
            "break_even_benefit": value_of_time / (votes_per_hour * p)}


def summary(probabilities: dict[str, float], n_people: int) -> dict:
    """The break-even figures for the national average voter, for each event (name -> p)."""
    out = {"value_of_time": VALUE_OF_TIME, "minutes": MINUTES, "cost": COST,
           "votes_per_hour": list(VOTES_PER_HOUR), "population": n_people}
    for name, p in probabilities.items():
        b_star = break_even_benefit(p)
        out[name] = {
            "p": p,
            "break_even_benefit": b_star,
            # social benefit: p·N per euro of b at α = 1, and the α needed for b = 100 €
            "p_times_n": p * n_people,
            "alpha_for_b_100": float(break_even_alpha(p, n_people, np.array([100.0]))[0]),
            "alpha_for_b_1000": float(break_even_alpha(p, n_people, np.array([1000.0]))[0]),
            "influence": [influence(p, v) for v in VOTES_PER_HOUR],
        }
    return out
