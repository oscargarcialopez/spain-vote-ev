"""Run the backtests, the 2026 forecast, the power indices and the theory, and write
results/summary.json: the only source of the numbers quoted in the README, the carousel and
the post (`voteev check` verifies them)."""

from __future__ import annotations

import json
from datetime import date

import numpy as np
import pandas as pd

from . import backtest, completeness, investiture, model, parties, power, theory
from .provinces import NAME
from .sources import ELECTION_DATE, RESULTS

N = 100_000
SENSITIVITY_N = 20_000
ROBUSTNESS_N = 50_000  # each sensitivity of the robustness table, with one-vote odds
POWER_SAMPLE = 10_000
GSE_2012_ONE_IN = 60_000_000  # Gelman, Silver and Edlin (2012), the 2008 US average
PARTY_FIRMS = {"PP", "PSOE", "Vox", "Sumar", "Podemos", "SALF", "ERC", "Junts", "PNV",
               "EH Bildu", "BNG", "CC", "Frente Amplio"}


# Investiture rules compared with the base rule (investiture.py), on the same simulated seats.
GOV_VARIANTS = {"no_record_abstain": {"no_record": "abstain"}}


def one_in(p: float) -> float | None:
    return float(1 / p) if p > 0 else None


def government(setup: model.Setup, seats_f: np.ndarray, b: investiture.Behaviour) -> dict:
    """Who is invested in each simulated Congress, in which vote, and whose votes it needed."""
    F, K = setup.F, len(setup.labels)  # noqa: N806
    seats = np.zeros((len(seats_f), K), np.int32)
    seats[:, :F] = seats_f
    yes, no, own = investiture.tallies(seats, b)
    who, stage = investiture.outcome(yes, no, own)
    passes = (yes >= investiture.MAJORITY) | (yes > no)
    nec = investiture.necessary(seats, b, who)[:, :F]
    out = {"rule": b.name, "votes": b.table(), "blocked": float((who == 0).mean()),
           "second_vote": float((stage == 2).mean()),
           "both_possible": float(passes.all(axis=1).mean()), "candidates": {}, "keys": {}}
    for c, cand in enumerate(investiture.CANDIDATES):
        mine = who == c + 1
        out["candidates"][cand] = {
            "p": float(mine.mean()), "first_vote": float((mine & (stage == 1)).mean()),
            "second_vote": float((mine & (stage == 2)).mean()),
            "yes_mean": float(yes[:, c].mean()),
            "yes_lo80": backtest.interval(yes[:, c], 0.8)[0],
            "yes_hi80": backtest.interval(yes[:, c], 0.8)[1]}
    for j, f in enumerate(setup.families):
        k = {cand: float((nec[:, j] & (who == c + 1)).mean())
             for c, cand in enumerate(investiture.CANDIDATES)}
        out["keys"][f] = {**k, "any": float(nec[:, j].mean())}
    return out


def seat_table(setup: model.Setup, sim: model.SimResult) -> dict:
    out = {}
    for j, f in enumerate(setup.families):
        x = sim.seats[:, j]
        lo80, hi80 = backtest.interval(x, 0.8)
        lo95, hi95 = backtest.interval(x, 0.95)
        out[f] = {"name": parties.DISPLAY.get(f, f), "share": float(setup.national[j]),
                  "base_share": float(setup.base_national[j]), "polled": bool(setup.polled[j]),
                  "mean": float(x.mean()), "median": float(np.median(x)),
                  "lo80": lo80, "hi80": hi80, "lo95": lo95, "hi95": hi95,
                  "p_any_seat": float((x > 0).mean()),
                  "constituencies": int(setup.present[:, j].sum())}
    return out


def bloc_table(setup: model.Setup, sim: model.SimResult) -> dict:
    out = {}
    for b, name in enumerate(sim.bloc_names):
        x = sim.blocs[:, b]
        lo80, hi80 = backtest.interval(x, 0.8)
        lo95, hi95 = backtest.interval(x, 0.95)
        out[name] = {"members": list(model.BLOCS[setup.key][name]), "mean": float(x.mean()),
                     "median": float(np.median(x)), "lo80": lo80, "hi80": hi80,
                     "lo95": lo95, "hi95": hi95,
                     "p_majority": float((x >= parties.MAJORITY).mean()),
                     "p_exactly_175_or_176": float(np.isin(x, (175, 176)).mean())}
    return out


def vote_probabilities(setup: model.Setup, sim: model.SimResult) -> dict:
    """P(one extra vote changes a seat / a bloc's majority status), for the average voter of
    each constituency and of Spain, weighting each list by its expected votes."""
    F, n = setup.F, sim.n
    w = sim.votes[:, :F]
    events = {"seat": sim.flips}
    for b, name in enumerate([*sim.bloc_names, "any"]):
        events[f"majority_{name}"] = sim.pivots[..., b]
    if sim.gov_pivots is not None:
        events["government"] = sim.gov_pivots
    out = {"bandwidths": list(model.H_MULTS), "default_bandwidth": model.H_DEFAULT,
           "national": {}, "provinces": [], "by_list": {}}
    hd = model.H_MULTS.index(model.H_DEFAULT)
    for ev, counts in events.items():
        dens = counts / (n * sim.h[:, None, :])                      # (I, F, H)
        nat = np.einsum("if,ifh->h", w, dens) / w.sum()
        se = np.sqrt(np.einsum("ifh,ifh->h", (w[..., None] / (n * sim.h[:, None, :])) ** 2,
                               counts)) / w.sum()
        out["national"][ev] = {
            "p": float(nat[hd]), "one_in": one_in(nat[hd]), "mc_se": float(se[hd]),
            "by_bandwidth": {str(m): float(nat[k]) for k, m in enumerate(model.H_MULTS)},
            "events_counted": int(counts[..., hd].sum())}
        prov = np.einsum("if,if->i", w, dens[..., hd]) / w.sum(axis=1)
        for i, code in enumerate(setup.codes):
            if len(out["provinces"]) <= i:
                out["provinces"].append({
                    "code": code, "name": NAME[code], "seats": int(setup.seats[i]),
                    "electors": int(setup.electors[i]),
                    "electors_per_seat": float(setup.electors[i] / setup.seats[i]),
                    "expected_valid_votes": float(setup.weights[i])})
            out["provinces"][i][f"p_{ev}"] = float(prov[i])
            out["provinces"][i][f"one_in_{ev}"] = one_in(prov[i])
        by_list = (w * dens[..., hd]).sum(axis=0) / w.sum(axis=0)
        for j, f in enumerate(setup.families):
            out["by_list"].setdefault(f, {})[ev] = float(by_list[j])
    return out


def poll_info(setup: model.Setup) -> dict:
    cols = [c for c in setup.window.columns if c not in ("poll", *model.polls.META)]
    window = [{"firm": r["label"], "end": r["end"].isoformat(),
               "sample": None if pd.isna(r["sample"]) else int(r["sample"]),
               **{c: float(r[c]) for c in cols if pd.notna(r[c])}}
              for _, r in setup.window.iterrows()]
    return {"cutoff": setup.cutoff.isoformat(), "lead_days": setup.lead,
            "window_days": model.polls.WINDOW_DAYS, "firms": len(setup.window),
            "medians": setup.poll_medians, "window": window,
            "party_released": sorted(set(setup.window["firm"]) & PARTY_FIRMS)}


def cis_comparison(setup: model.Setup) -> dict | None:
    """The CIS's latest own estimate against the median of the other firms over the 14 days
    to the end of the CIS's fieldwork."""
    wide = model.poll_wide("2026")
    cis = wide[(wide["firm"] == "CIS") & (wide["end"] <= setup.cutoff)]
    if cis.empty:
        return None
    own = cis[cis["label"] == "CIS"]
    row = (own if not own.empty else cis).sort_values("end").iloc[-1]
    target = model.TARGETS["2026"]
    others = model.polls.window(wide[wide["firm"] != "CIS"], row["end"])
    out = {"end": row["end"].isoformat(), "label": row["label"], "others": len(others),
           "lists": {}}
    for f in target.families:
        spec = target.poll_spec.get(f, {"cols": [f]})
        mine = model._family_values(pd.DataFrame([row]), spec)
        theirs = model._family_values(others, spec)
        if mine and len(theirs) >= model.MIN_FIRMS:
            out["lists"][f] = {"cis": mine[0], "others_median": float(np.median(theirs)),
                               "difference": mine[0] - float(np.median(theirs))}
    return out


def manifest_revisions() -> dict:
    from .download import read_manifest
    return {k: v["note"].replace("revid=", "") for k, v in read_manifest().items()
            if v["note"].startswith("revid=")}


def headline(setup: model.Setup, sim: model.SimResult, b: investiture.Behaviour) -> dict:
    """The numbers a sensitivity is compared on: who is invested, and the one-vote odds."""
    g = government(setup, sim.seats, b)
    out = {"PP": g["candidates"]["PP"]["p"], "PSOE": g["candidates"]["PSOE"]["p"],
           "blocked": g["blocked"], "second_vote": g["second_vote"],
           "seats": {f: float(sim.seats[:, j].mean()) for j, f in enumerate(setup.families)}}
    if sim.flips is not None:
        nat = vote_probabilities(setup, sim)["national"]
        out["seat_one_in"] = nat["seat"]["one_in"]
        out["government_one_in"] = nat["government"]["one_in"]
    return out


def robustness(setup: model.Setup, calib: model.Calibration, factor: float, sigma_df: int | None,
               base: dict, n: int = ROBUSTNESS_N) -> list[dict]:
    """The forecast redone with one thing changed at a time (the robustness table)."""
    rows = [{"key": "base", "group": "base", **base}]
    rule = investiture.behaviour(setup.labels)

    def run_one(key, group, s=setup, b=rule, df=sigma_df, note=None):
        print(f"  {key} ...")
        sim = model.simulate(s, calib, n=n, widen=factor, track=True, behaviour=b, sigma_df=df)
        rows.append({"key": key, "group": group, "firms": len(s.window), "n": n,
                     "note": note, **headline(s, sim, b)})

    for agg in model.AGGREGATIONS[1:]:
        s2 = model.build("2026", cutoff=setup.cutoff, aggregation=agg)
        if agg == "no_cis" and "CIS" not in set(setup.window["firm"]):
            rows.append({"key": agg, "group": "polls", "note": "no CIS poll in the window",
                         "same_as_base": True})
            continue
        run_one(agg, "polls", s=s2)
    party = tuple(sorted(set(setup.window["firm"]) & PARTY_FIRMS))
    if party:
        run_one("no_party_polls", "polls",
                s=model.build("2026", cutoff=setup.cutoff, exclude_firms=party),
                note=", ".join(party))
    run_one("normal_errors" if sigma_df else "student_t", "errors",
            df=None if sigma_df else calib.n_errors)
    for name, kw in GOV_VARIANTS.items():
        run_one(name, "investiture", b=investiture.behaviour(setup.labels, name=name, **kw))
    return rows


def run(n: int = N, cutoff: date | None = None, backtest_n: int = backtest.N) -> dict:
    print("backtests (pre-declared rule) ...")
    bt = backtest.run(n=backtest_n)
    factor = bt["chosen_factor"]
    print(f"  factor {factor}")
    setup = model.build("2026", cutoff=cutoff)
    calib = model.calibrate("2026", setup.lead)
    print(f"σ's own uncertainty: four backtests at the {setup.lead}-day lead ...")
    srule = backtest.sigma_rule(factor, setup.lead, n=backtest_n)
    sigma_df = calib.n_errors if srule["adopt_student_t"] else None
    print(f"  Student-t errors adopted: {srule['adopt_student_t']}")
    print(f"2026: cutoff {setup.cutoff}, {len(setup.window)} firms, lead {setup.lead} days; "
          f"simulating {n:,} ...")
    rule = investiture.behaviour(setup.labels)
    sim = model.simulate(setup, calib, n=n, widen=factor, track=True, behaviour=rule,
                         sigma_df=sigma_df)
    gov = government(setup, sim.seats, rule)
    gov["variants"] = {
        name: {k: v for k, v in government(setup, sim.seats, investiture.behaviour(
            setup.labels, name=name, **kw)).items() if k not in ("votes",)}
        for name, kw in GOV_VARIANTS.items()}
    adopted = "student_t" if sigma_df else "normal"
    bt_lead = [r for r in srule[adopted]["runs"] if r["election"] in backtest.BACKTESTS]
    print("sensitivity without party-released polls ...")
    party = tuple(sorted(set(setup.window["firm"]) & PARTY_FIRMS))
    sens = None
    if party:
        s2 = model.build("2026", cutoff=setup.cutoff, exclude_firms=party)
        sim2 = model.simulate(s2, calib, n=SENSITIVITY_N, widen=factor, track=False)
        sens = {"excluded": list(party), "firms": len(s2.window),
                "seats": {f: v["mean"] for f, v in seat_table(s2, sim2).items()},
                "blocs": {b: v["p_majority"] for b, v in bloc_table(s2, sim2).items()}}
    print("robustness ...")
    rob = robustness(setup, calib, factor, sigma_df, headline(setup, sim, rule))
    print("power indices ...")
    ss, bz, sample = power.over_simulations(sim.seats, POWER_SAMPLE)
    seats_2023 = parties.SEATS_2023
    ss23, bz23 = power.indices(list(seats_2023.values()))
    votes = vote_probabilities(setup, sim)
    context = model.data()["context"]
    pop = context["population"]["population"]
    nat = votes["national"]
    summary = {
        "meta": {"election": ELECTION_DATE["2026"], "n": n, "seed": model.SEED,
                 "widen_factor": factor, "threshold": 0.03, "majority": parties.MAJORITY,
                 "min_firms": model.MIN_FIRMS, "rake_iterations": model.RAKE_ITERS,
                 "student_t": bool(sigma_df), "sigma_df": sigma_df,
                 "wikipedia_revisions": manifest_revisions()},
        "polls": poll_info(setup),
        "cis": cis_comparison(setup),
        "calibration": calib.as_dict(),
        "poll_errors": calib.errors.to_dict("records"),
        "lists": seat_table(setup, sim),
        "blocs": bloc_table(setup, sim),
        "vote": votes,
        "power": {
            "sample": sample,
            "simulated": {f: {"seat_share": float(sim.seats[:, j].mean() / 350),
                              "shapley_shubik": float(ss[j]), "banzhaf": float(bz[j])}
                          for j, f in enumerate(setup.families)},
            "congress_2023": {p: {"seats": s, "seat_share": s / 350,
                                  "shapley_shubik": float(a), "banzhaf": float(b)}
                              for (p, s), a, b in zip(seats_2023.items(), ss23, bz23,
                                                      strict=True)}},
        "government": gov,
        "theory": theory.summary({"seat": nat["seat"]["p"], "majority": nat["majority_any"]["p"],
                                  "government": nat["government"]["p"]}, pop),
        "backtest": {"rule": bt["rule"], "chosen_factor": factor,
                     "tried": [{k: v for k, v in t.items() if k != "runs"} for t in bt["tried"]],
                     "runs": next(t["runs"] for t in bt["tried"] if t["factor"] == factor),
                     "at_2026_lead": {"lead_days": setup.lead, "runs": bt_lead,
                                      **backtest.coverage(bt_lead)},
                     "sigma_rule": {k: v for k, v in srule.items()}},
        "robustness": rob,
        "completeness": completeness.check(),
        "sensitivity_party_polls": sens,
        "context": {**context, "gse_2012_one_in": GSE_2012_ONE_IN},
    }
    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / "summary.json").write_text(json.dumps(summary, indent=1, ensure_ascii=False,
                                                     default=_json))
    prov = pd.DataFrame(votes["provinces"])
    prov.to_csv(RESULTS / "provinces.csv", index=False, float_format="%.6g")
    seats = pd.DataFrame(sim.prov_seats, columns=setup.families, index=setup.codes)
    seats.insert(0, "name", [NAME[c] for c in setup.codes])
    seats.to_csv(RESULTS / "seats_by_province.csv", index_label="code", float_format="%.3f")
    print(f"-> {RESULTS / 'summary.json'}")
    return summary


def _json(x):
    if isinstance(x, (np.integer,)):
        return int(x)
    if isinstance(x, (np.floating,)):
        return float(x)
    if isinstance(x, (np.bool_,)):
        return bool(x)
    if isinstance(x, (date,)):
        return x.isoformat()
    raise TypeError(type(x))
