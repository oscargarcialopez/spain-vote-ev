"""The README's tables, generated from results/summary.json through facts.build(), so they are
right by construction. `voteev tables` rewrites each block between its markers:

    <!-- BEGIN provinces -->
    ...
    <!-- END provinces -->

The prose around them is written by hand and checked with `voteev check`.
"""

from __future__ import annotations

import re
from pathlib import Path

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
                     f[f"{k}.majority"], f[f"{k}.F"], f[f"{k}.S"], f[f"{k}.S_no_JUNTS"]])
    return _table(["Constituency", "Seats", "Electors per seat", "Seat: 1 in",
                   "Either bloc to 176: 1 in", "F: 1 in", "S: 1 in", "S without Junts: 1 in"],
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


BLOCKS = {"provinces": provinces, "lists": lists, "blocs": blocs, "power": power,
          "backtests": backtests, "cis": cis, "polls": polls}


def update(readme: Path, s: dict) -> list[str]:
    f = fx.build(s)
    text = Path(readme).read_text()
    done = []
    for name, make in BLOCKS.items():
        pat = re.compile(rf"(<!-- BEGIN {name} -->\n)(?:.*?\n)?(<!-- END {name} -->)", re.S)
        if pat.search(text):
            body = make(s, f)
            text = pat.sub(lambda m, body=body: m.group(1) + body + "\n" + m.group(2), text)
            done.append(name)
    Path(readme).write_text(text)
    return done
