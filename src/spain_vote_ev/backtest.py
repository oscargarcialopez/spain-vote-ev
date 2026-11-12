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
"""

from __future__ import annotations

import numpy as np

from . import model

BACKTESTS = ("2019N", "2023")
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


def run_one(key: str, factor: float = 1.0, lead: int = LEAD, n: int = N) -> dict:
    setup = model.build(key, lead=lead)
    calib = model.calibrate(key, setup.lead)
    sim = model.simulate(setup, calib, n=n, widen=factor, track=False)
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
            "firms": len(setup.window), "factor": factor, "calibration": calib.as_dict(),
            "lists": lists, "blocs": blocs, "unmodelled_seats": int(
                model.data()["results"].query("election == @key")["seats"].sum() - actual.sum())}


def coverage(runs: list[dict]) -> dict:
    counted = [x for r in runs for x in r["lists"] if x["counted"]]
    return {"lists": len(counted),
            "in80": sum(x["in80"] for x in counted), "in95": sum(x["in95"] for x in counted),
            "cov80": sum(x["in80"] for x in counted) / len(counted),
            "cov95": sum(x["in95"] for x in counted) / len(counted)}


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
