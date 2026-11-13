"""The README's tables, generated from results/summary.json through facts.build(), so they are
right by construction: the README template places each one with {{table:name}} (texts.py).
"""

from __future__ import annotations

from . import facts as fx
from .parties import DISPLAY


def _table(header: list[str], align: str, rows: list[list[str]]) -> str:
    sep = ["---:" if a == "r" else ":---:" if a == "c" else "---" for a in align]
    lines = ["| " + " | ".join(header) + " |", "| " + " | ".join(sep) + " |"]
    lines += ["| " + " | ".join(r) + " |" for r in rows]
    return "\n".join(lines)


def provinces(s: dict, f: dict) -> str:
    rows = []
    for r in sorted(s["vote"]["provinces"], key=lambda r: r["p_seat"], reverse=True):
        k = f"prov.{r['name']}"
        rows.append([r["name"], f[f"{k}.seats"], f[f"{k}.eps"], f[f"{k}.seat"],
                     f[f"{k}.government"], f[f"{k}.majority"], f[f"{k}.F"], f[f"{k}.S"]])
    return _table(["Constituency", "Seats", "Electors per seat", "Seat: 1 in",
                   "Who is invested: 1 in", "Either bloc to 176: 1 in", "F: 1 in", "S: 1 in"],
                  "lrrrrrrr", rows)


def lists(s: dict, f: dict) -> str:
    rows = []
    for code, x in sorted(s["lists"].items(), key=lambda kv: -kv[1]["mean"]):
        rows.append([x["name"], f[f"{code}.share"], f[f"{code}.seats"], f[f"{code}.i80"],
                     f[f"{code}.i95"], f[f"{code}.p_seat"]])
    return _table(["List", "Vote share (centre)", "Mean seats", "80%", "95%",
                   "P(at least one seat)"], "lrrccr", rows)


def blocs(s: dict, f: dict) -> str:
    names = {"F": "F", "S": "S", "S_no_JUNTS": "S without Junts"}
    rows = [[names[b], f[f"bloc.{b}.mean"], f[f"bloc.{b}.i80"], f[f"bloc.{b}.i95"],
             f[f"bloc.{b}.p1"], f[f"majority_{b}.one_in"]] for b in s["blocs"]]
    return _table(["Bloc", "Mean seats", "80%", "95%", "P(≥ 176)",
                   "One vote moves it across 176: 1 in"], "lrccrr", rows)


def power(s: dict, f: dict) -> str:
    rows = [[DISPLAY.get(p, p), str(x["seats"]), f[f"pw23.{p}.seats"], f[f"pw23.{p}.ss"],
             f[f"pw23.{p}.bz"]] for p, x in s["power"]["congress_2023"].items()]
    a = _table(["List", "Seats", "Seat share", "Shapley–Shubik", "Banzhaf"], "lrrrr", rows)
    rows = [[DISPLAY.get(p, p), f[f"pw.{p}.seats"], f[f"pw.{p}.ss"], f[f"pw.{p}.bz"]]
            for p, x in sorted(s["power"]["simulated"].items(),
                               key=lambda kv: -kv[1]["seat_share"])
            if x["seat_share"] >= 0.001]
    b = _table(["List", "Mean seat share", "Shapley–Shubik", "Banzhaf"], "lrrr", rows)
    return ("The 2023 Congress:\n\n" + a + "\n\nAveraged over " + f["pw.sample"] +
            " simulated 2026 parliaments (lists with at least 0.1% of the seats):\n\n" + b)


def backtests(s: dict, f: dict) -> str:
    rows = []
    for run in s["backtest"]["runs"]:
        e = run["election"]
        name = "Nov 2019" if e == "2019N" else e
        for x in run["lists"]:
            if not x["counted"]:
                continue
            lo, hi = f[f"bt.{e}.{x['list']}"].split(" in ")
            mark = "" if x["in80"] else (" (outside 80%)" if x["in95"] else " (outside 95%)")
            rows.append([name, DISPLAY.get(x["list"], x["list"]), lo + mark, hi,
                         f[f"bt.{e}.{x['list']}.i95"]])
    return _table(["Election", "List", "Actual seats", "80%", "95%"], "llrcc", rows)


def cis(s: dict, f: dict) -> str:
    c = s.get("cis")
    if not c:
        return "No CIS poll in the data."
    rows = [[DISPLAY.get(p, p), f[f"cis.{p}"], f[f"cis.{p}.others"], f[f"cis.{p}.diff"]]
            for p in c["lists"]]
    return _table(["List", "CIS (%)", "Median of the other firms (%)", "Difference (points)"],
                  "lrrr", rows)


def polls(s: dict, f: dict) -> str:
    rows = [[DISPLAY.get(k, k), f[f"poll.{k}"], f[f"poll.{k}.range"], f[f"poll.{k}.firms"]]
            for k in s["polls"]["medians"]]
    return _table(["List", "Median (%)", "Range across firms (%)", "Firms"], "lrcr", rows)


def government(s: dict, f: dict) -> str:
    g = s["government"]
    rows = [[f"The {c}'s candidate", f[f"gov.{c}.yes"], f[f"gov.{c}.yes80"], f[f"gov.{c}.p1"],
             f[f"gov.{c}.first"], f[f"gov.{c}.second"]] for c in g["candidates"]]
    rows.append(["Nobody", "", "", f["gov.blocked"], "", ""])
    return _table(["Candidate", "Yes votes (mean)", "80%", "Invested", "In the first vote",
                   "Only in the second vote"], "lrcrrr", rows)


def keys(s: dict, f: dict) -> str:
    k, pw = s["government"]["keys"], s["power"]["simulated"]
    shown = sorted((x for x in k if x in pw and s["lists"][x]["mean"] >= 0.5),
                   key=lambda x: -s["lists"][x]["mean"])
    rows = [[DISPLAY.get(x, x), f[f"{x}.seats"], f[f"pw.{x}.ss"], f[f"pw.{x}.bz"],
             f[f"key.{x}.PP"], f[f"key.{x}.PSOE"], f[f"key.{x}.any"]] for x in shown]
    return _table(["List", "Mean seats", "Shapley–Shubik", "Banzhaf", "Key: the PP's candidate",
                   "Key: the PSOE's candidate", "Key: either"], "lrrrrrr", rows)


ROBUSTNESS = {
    "base": "Base: median of each list across firms",
    "weighted_mean": "Mean weighted by sample size",
    "days7": "Each firm's latest poll in the last 7 days only",
    "house2023": "Each firm's shares corrected by its 2023 error (house effect)",
    "no_cis": "Without the CIS",
    "no_party_polls": "Without polls released by a party",
    "normal_errors": "Normal national errors (no Student-t)",
    "student_t": "Student-t national errors",
    "no_record_abstain": "Lists with no 2023 seat abstain instead of voting no",
}


def robustness(s: dict, f: dict) -> str:
    rows = []
    for r in s["robustness"]:
        k = r["key"]
        if r.get("same_as_base"):
            rows.append([ROBUSTNESS[k], "", "", "", "", "", "", r["note"]])
            continue
        rows.append([ROBUSTNESS[k], str(r.get("firms", f["firms"])), f[f"rob.{k}.PP"],
                     f[f"rob.{k}.PSOE"], f[f"rob.{k}.blocked"], f[f"rob.{k}.second"],
                     f[f"rob.{k}.gov"], r.get("note") or ""])
    return _table(["Variant", "Firms", "The PP's candidate", "The PSOE's candidate", "Nobody",
                   "Only in the second vote", "One vote changes who: 1 in", "Note"],
                  "lrrrrrrl", rows)


def sigma_rule(s: dict, f: dict) -> str:
    sr = s["backtest"]["sigma_rule"]
    rows = []
    for e in sr["normal"]["by_election"]:
        rows.append([f[f"sr.{e}.name"], f[f"sr.{e}.cutoff"], f[f"sr.{e}.firms"],
                     f[f"sr.{e}.sigma"], f[f"sr.{e}.n_errors"], f[f"sr.n.{e}.in80"],
                     f[f"sr.n.{e}.in95"], f[f"sr.t.{e}.in80"], f[f"sr.t.{e}.in95"]])
    rows.append(["All four", "", "", "", "", f["sr.n.in80"], f["sr.n.in95"], f["sr.t.in80"],
                 f["sr.t.in95"]])
    return _table(["Election", "Cutoff", "Firms", "σ", "Past errors", "Normal: in 80%",
                   "Normal: in 95%", "Student-t: in 80%", "Student-t: in 95%"],
                  "llrrrrrrr", rows)


def completeness(s: dict, f: dict) -> str:
    c = s.get("completeness")
    if not c:
        return "Not computed."
    rows = [[r["constituency"], r["list"], f[f"comp.{i}.share"],
             fx.ELECTIONS[r["best_election"]][0], f[f"comp.{i}.min"]]
            for i, r in enumerate(c["with_a_past_result"][:10], start=1)]
    return _table(["Constituency", "2026 candidacy", "Best past share", "In",
                   "Smallest share that won a seat there"], "llrlr", rows)


def record(s: dict, f: dict) -> str:
    """Every investiture vote since 2016 and the 2018 censure motion, from the Diario de
    Sesiones (data/curated/investitures.csv)."""
    rows = []
    for i, v in enumerate(s["context"]["record"], start=1):
        k = f"rec.{i}"
        name = v["candidate"].split()[-1]
        vote = ("censure motion" if v["kind"] == "censure" else
                "first" if v["round"] == 1 else "second")
        doc = v["url"].rsplit("/", 1)[-1].removesuffix(".PDF")
        rows.append([f[f"{k}.date"], f"{name} ({v['party']})", vote, f[f"{k}.yes"],
                     f[f"{k}.no"], f[f"{k}.abstain"], f[f"{k}.absent"],
                     "yes" if v["passed"] else "no", f[f"{k}.yes_from"],
                     f[f"{k}.abstained"], f"[{doc}]({v['url']})"])
    return _table(["Date", "Candidate", "Vote", "Yes", "No", "Abstained", "Other",
                   "Invested", "Yes votes", "Abstentions", "Diario de Sesiones"],
                  "lllrrrrllll", rows)


BLOCKS = {"record": record, "provinces": provinces, "lists": lists, "blocs": blocs,
          "power": power, "backtests": backtests, "cis": cis, "polls": polls,
          "government": government, "keys": keys, "robustness": robustness,
          "sigma_rule": sigma_rule, "completeness": completeness}
