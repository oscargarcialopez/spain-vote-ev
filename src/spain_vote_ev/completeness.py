"""Is every list that could win a seat in the model? A check against the 2026 candidacies.

The model simulates the lists polled by at least MIN_FIRMS firms and the local lists with a
2023 result (model.TARGETS); every other 2026 candidacy is in 'others', which wins no seat.
For each of those candidacies this finds the best share that a list of the same name won in
the same constituency in a general election since 2015, and the smallest share that has won
a seat there in those elections. A candidacy is flagged when its best past share reaches that
smallest winning share: it would have to be modelled. It also lists the poll columns that
fewer than MIN_FIRMS firms report (a list polled too little to be simulated from the polls).
"""

from __future__ import annotations

import re
import unicodedata

import pandas as pd

from . import model
from .provinces import NAME
from .sources import PROCESSED

STOP = {"COALICION", "COALICIO", "AGRUPACION", "ELECTORES", "DE", "DEL", "LA", "EL", "LOS",
        "LAS", "Y", "I", "E", "EN", "POR", "PER", "AL", "A", "PARTIDO", "PARTIT", "CON"}


def _norm(text: str) -> str:
    text = unicodedata.normalize("NFKD", str(text or ""))
    return "".join(c for c in text if not unicodedata.combining(c)).upper()


def tokens(name: str) -> frozenset[str]:
    """The distinctive words of a list's name, without its abbreviation in brackets."""
    words = re.findall(r"[A-Z0-9]+", re.sub(r"\([^)]*\)", " ", _norm(name)))
    return frozenset(w for w in words if w not in STOP and len(w) > 1)


def same_list(name: str, abbr: str, past_name: str, past_abbr: str) -> bool:
    a, b = _norm(abbr).strip(), _norm(past_abbr).strip()
    if len(a) >= 2 and a == b:
        return True
    t, u = tokens(name), tokens(past_name)
    small = min(len(t), len(u))
    return small >= 2 and (t <= u or u <= t)


def check() -> dict:
    cand = pd.read_csv(PROCESSED / "candidacies_2026.csv", dtype={"code": str})
    past = pd.read_csv(PROCESSED / "list_results.csv", dtype={"code": str})
    summ = pd.read_csv(PROCESSED / "summary.csv", dtype={"code": str})
    valid = summ.set_index(["election", "code"])["valid"]
    past["share"] = past["votes"] / [valid[(e, c)] for e, c in zip(past["election"],
                                                                     past["code"], strict=True)]
    min_win = past[past["seats"] > 0].groupby("code")["share"].min()
    others = cand[cand["label"] == "OTH"]
    found = []
    for _, c in others.iterrows():
        same = past[past["code"] == c["code"]]
        hits = same[[same_list(c["name"], c["abbr"], n, a)
                     for n, a in zip(same["list"], same["abbr"].fillna(""), strict=True)]]
        if hits.empty:
            continue
        best = hits.loc[hits["share"].idxmax()]
        found.append({"code": c["code"], "constituency": NAME[c["code"]], "list": c["name"],
                      "best_share": float(best["share"]), "best_election": best["election"],
                      "best_seats": int(best["seats"]),
                      "min_winning_share": float(min_win[c["code"]]),
                      "flagged": bool(best["share"] >= min_win[c["code"]])})
    window = model.build("2026").window
    cols = [c for c in window.columns if c not in ("poll", *model.polls.META)]
    few = {c: int(window[c].notna().sum()) for c in cols
           if 0 < window[c].notna().sum() < model.MIN_FIRMS}
    return {"candidacies": int(len(cand)), "in_others": int(len(others)),
            "with_a_past_result": sorted(found, key=lambda r: -r["best_share"]),
            "flagged": [r for r in found if r["flagged"]],
            "poll_columns_below_min_firms": few}
