"""Backtests: the whole method run as it would have been seven days before the November 2019
and the July 2023 elections, each calibrated only on the elections before it.

PRE-DECLARED RULE (committed before the first backtest was run; not changed afterwards):

    Lists counted: every list that won at least one seat in the actual result or in its base
    election. Pool the lists of both backtests. If fewer than 75% of the actual seat counts
    fall inside their 80% intervals, or fewer than 90% inside their 95% intervals, multiply
    every error standard deviation (national, CCAA, constituency, turnout) by the smallest
    factor in (1.25, 1.5, 2.0) that meets both targets, or by 2.0 if none does. The 2026
    forecast uses the same factor. Intervals are central quantile intervals of the simulated
    seats, inclusive at both ends.

Blocs used to place the actual majority outcome: 2023, the two investiture coalitions of that
legislature (as for 2026); November 2019, the lists whose deputies voted for the investiture
of 7 January 2020 (PSOE, Unidas Podemos, PNV, Más País, BNG).

PRE-DECLARED RULE FOR THE UNCERTAINTY OF σ ITSELF (written on 12 Nov 2026, before the runs
that apply it; added in Phase 2 with two more backtests, June 2016 and April 2019):

    σ is estimated from a few dozen past errors, so it is uncertain itself. The alternative
    draws the national scale in each simulation from its sampling distribution, σ²·n/χ²(n)
    with n the number of past errors (Student-t national errors). Run the four backtests (2016,
    April 2019, November 2019, 2023) at the publication lead of the forecast, with the factor
    chosen above, with normal and with Student-t errors. Distance to nominal = |coverage of the
    80% intervals − 80%| + |coverage of the 95% intervals − 95%|, over the counted lists.
    Adopt the alternative for the forecast if it lowers the distance pooled over the four
    backtests and does not raise it over the November 2019 and 2023 pair (the two reported
    before); otherwise report it as a sensitivity. The 2016 backtest borrows its provincial
    and turnout spreads from later elections (model.calibrate), so it is partly in sample.
"""

from __future__ import annotations

import numpy as np

from . import model

BACKTESTS = ("2019N", "2023")
ALL_BACKTESTS = ("2016", "2019A", "2019N", "2023")
LEAD = 7
N = 20_000
TARGET_80, TARGET_95 = 0.75, 0.90
FACTORS = (1.0, 1.25, 1.5, 2.0)


def interval(x: np.ndarray, level: float) -> tuple[int, int]:
    a = (1 - level) / 2
    return (int(np.quantile(x, a, method="inverted_cdf")),
            int(np.quantile(x, 1 - a, method="inverted_cdf")))


def base_seats(target: model.Target) -> dict[str, int]:
    r = model.data()["results"]
    r = r[r["election"] == target.base]
    inv = {lab: fam for fam, labs in target.base_map.items() for lab in labs}
    out = dict.fromkeys(target.families, 0)
    for lab, seats in r.groupby("label")["seats"].sum().items():
        if lab in inv:
            out[inv[lab]] += int(seats)
    return out


def run_one(key: str, factor: float = 1.0, lead: int = LEAD, n: int = N,
            student_t: bool = False) -> dict:
    setup = model.build(key, lead=lead)
    calib = model.calibrate(key, setup.lead)
    sim = model.simulate(setup, calib, n=n, widen=factor, track=False,
                         sigma_df=calib.n_errors if student_t else None)
    actual = setup.actual_seats.sum(axis=0)
    before = base_seats(model.TARGETS[key])
    lists = []
    for j, f in enumerate(setup.families):
        x = sim.seats[:, j]
        lo80, hi80 = interval(x, 0.80)
        lo95, hi95 = interval(x, 0.95)
        a = int(actual[j])
        lists.append({
            "list": f, "actual": a, "mean": float(x.mean()), "median": float(np.median(x)),
            "lo80": lo80, "hi80": hi80, "lo95": lo95, "hi95": hi95,
            "in80": lo80 <= a <= hi80, "in95": lo95 <= a <= hi95,
            "counted": bool(a > 0 or before[f] > 0),
            "poll_median": setup.poll_medians.get(f, {}).get("median"),
            "actual_share": float(100 * setup.actual_shares[j])})
    blocs = []
    for b, name in enumerate(sim.bloc_names):
        members = model.BLOCS[key][name]
        a = int(sum(actual[setup.families.index(f)] for f in members))
        x = sim.blocs[:, b]
        blocs.append({"bloc": name, "members": list(members), "actual": a,
                      "mean": float(x.mean()), "p_majority": float((x >= 176).mean()),
                      "actual_percentile": float((x < a).mean() + 0.5 * (x == a).mean()),
                      "lo80": interval(x, 0.8)[0], "hi80": interval(x, 0.8)[1],
                      "lo95": interval(x, 0.95)[0], "hi95": interval(x, 0.95)[1]})
    return {"election": key, "lead_days": setup.lead, "cutoff": setup.cutoff.isoformat(),
            "firms": len(setup.window), "factor": factor, "student_t": student_t,
            "calibration": calib.as_dict(),
            "lists": lists, "blocs": blocs, "unmodelled_seats": int(
                model.data()["results"].query("election == @key")["seats"].sum() - actual.sum())}


def coverage(runs: list[dict]) -> dict:
    counted = [x for r in runs for x in r["lists"] if x["counted"]]
    return {"lists": len(counted),
            "in80": sum(x["in80"] for x in counted), "in95": sum(x["in95"] for x in counted),
            "cov80": sum(x["in80"] for x in counted) / len(counted),
            "cov95": sum(x["in95"] for x in counted) / len(counted)}


def distance(cov: dict) -> float:
    return abs(cov["cov80"] - 0.80) + abs(cov["cov95"] - 0.95)


def sigma_rule(factor: float, lead: int, n: int = N) -> dict:
    """The pre-declared rule for σ's own uncertainty (module docstring)."""
    runs = {t: {k: run_one(k, factor, lead, n, student_t=t) for k in ALL_BACKTESTS}
            for t in (False, True)}
    out = {"lead_days": lead, "factor": factor}
    for t, name in ((False, "normal"), (True, "student_t")):
        all4 = coverage(list(runs[t].values()))
        pair = coverage([runs[t][k] for k in BACKTESTS])
        out[name] = {"all": {**all4, "distance": distance(all4)},
                     "pair": {**pair, "distance": distance(pair)},
                     "by_election": {k: coverage([r]) for k, r in runs[t].items()},
                     "runs": list(runs[t].values())}
    out["adopt_student_t"] = bool(
        out["student_t"]["all"]["distance"] < out["normal"]["all"]["distance"]
        and out["student_t"]["pair"]["distance"] <= out["normal"]["pair"]["distance"])
    return out


def run(lead: int = LEAD, n: int = N) -> dict:
    """Apply the pre-declared rule: the smallest factor that meets both coverage targets."""
    tried = []
    chosen = None
    for factor in FACTORS:
        runs = [run_one(k, factor, lead, n) for k in BACKTESTS]
        cov = coverage(runs)
        tried.append({"factor": factor, **cov, "runs": runs})
        if cov["cov80"] >= TARGET_80 and cov["cov95"] >= TARGET_95:
            chosen = factor
            break
    if chosen is None:
        chosen = FACTORS[-1]
    return {"rule": {"targets": {"cov80": TARGET_80, "cov95": TARGET_95},
                     "factors": list(FACTORS), "lead_days": lead, "n": n},
            "chosen_factor": chosen, "tried": tried}
