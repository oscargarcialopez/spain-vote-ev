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
their vote is left out: it is near zero in US general elections (Kalla and Broockman, 2018),
though not in France in 2012 (Pons, 2018). The extra voters per hour of door-to-door
canvassing come from European field experiments: their pooled effect, +0.78 points of
turnout per voter reached (Bhatti et al., 2019), at the only European pace on record, 7.2
minutes per opened door (Cantoni and Pons, 2021; taken as a pair's time, which the paper
leaves open: as one person's, every per-hour figure doubles), and 1.8 registered voters per
household in Spain (INE), is about 0.06 extra voters per canvasser-hour; US-sized effects at
that pace give 0.2. The low end is zero: no effect in France's 2012 presidential election
(Pons, 2018) or in Spain's only experiment (Murcia, 2011; Morales, Ramiro and
Jiménez-Buedo, 2023), and there mobilising never pays.
"""

from __future__ import annotations

import numpy as np

VALUE_OF_TIME = 10.0          # €/h
MINUTES = 30                  # to go to the polling station, queue, vote and come back
COST = VALUE_OF_TIME * MINUTES / 60   # € per vote
VOTES_PER_HOUR = (0.06, 0.2)  # extra voters per canvasser-hour: European central, high
# The European door-to-door evidence behind it (README, "Others' votes"): the pooled effect
# per voter reached, in points, with its 95% interval, over 8 experiments (Bhatti et al., 2019);
# minutes per opened door, taken as a pair's (Cantoni and Pons, 2021); registered voters per
# household (INE); voters reached per canvasser-hour; the US pooled effect over 71
# experiments (Green, McGrath and Aronow, 2013).
CANVASS = {"effect_pp": 0.78, "effect_lo": -0.16, "effect_hi": 1.71, "experiments": 8,
           "minutes_per_door": 7.2, "voters_per_household": 1.8, "voters_per_hour": 7.5,
           "us_effect_pp": 2.5, "us_experiments": 71}
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
           "votes_per_hour": list(VOTES_PER_HOUR), "canvass": CANVASS, "population": n_people}
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
