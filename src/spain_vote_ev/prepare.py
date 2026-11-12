"""Turn the raw downloads into the small tables the model reads (data/processed/).

results.csv          election, code, label, votes, seats: every list's votes by constituency,
                     labelled (parties.py); 'OTH' is every unlabelled list, computed as Cuadro
                     I's candidate votes minus the labelled lists, so totals always match.
summary.csv          Cuadro I: electors, voters, valid, candidate, blank, null votes.
list_results.csv     every list by name (2016: the lists that won seats), for completeness.py.
ep2024.csv           the 2024 European Parliament votes by province and label.
constituencies_2026  seats (decree), electors (INE) per constituency.
candidacies_2026     every Congreso list proclaimed for 2026, with its label.
polls.csv            every national poll (long format: one row per poll and party column).
poll_results.csv     the result row of each past election's poll table (same columns).
context.json         population, the 2023 investiture votes, 2023 seats.
"""

from __future__ import annotations

import json

import pandas as pd

from . import boe, parties, polls
from .provinces import CCAA, CODES, NAME
from .sources import ELECTION_DATE, POLL_PAGES, PROCESSED, RAW

RESULT_FILES = {
    "2015": ("BOE-A-2016-867.xml", None),
    "2016": (None, "BOE-A-2016-7133.pdf"),
    "2019A": ("BOE-A-2019-8070.xml", None),
    "2019N": ("BOE-A-2019-18147.xml", "BOE-A-2019-17344.pdf"),
    "2023": ("BOE-A-2023-18907.xml", "BOE-A-2023-18907.pdf"),
}


def official_results() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    lists, summaries, named_lists = [], [], []
    for e, (xml, pdf) in RESULT_FILES.items():
        if e == "2016":
            lst = boe.parse_pdf_seat_lists_2016(RAW / pdf)
            summ = boe.parse_pdf_summary(RAW / pdf, e)
        else:
            lst, summ = boe.parse_html(RAW / xml, e)
            if pdf:
                summ = boe.parse_pdf_summary(RAW / pdf, e)
        lst["label"] = [parties.label_for(e, n, a) for n, a in zip(lst["list"], lst["abbr"],
                                                                     strict=True)]
        named_lists.append(lst.assign(election=e)[
            ["election", "code", "list", "abbr", "label", "votes", "seats"]])
        named = lst[lst["label"] != "OTH"].groupby(["code", "label"], as_index=False)[
            ["votes", "seats"]].sum()
        # Every unlabelled list is 'others': Cuadro I's candidate votes minus the labelled
        # ones (this also covers 2016, whose lists without seats are not parsed).
        cand = summ.set_index("code")["candidates"]
        oth_seats = lst[lst["label"] == "OTH"].groupby("code")["seats"].sum()
        oth = (cand - named.groupby("code")["votes"].sum().reindex(cand.index, fill_value=0))
        if (oth < 0).any():
            bad = list(oth[oth < 0].index)
            raise ValueError(f"{e}: labelled lists exceed candidate votes in {bad}")
        others = pd.DataFrame({"code": oth.index, "label": "OTH", "votes": oth.values,
                               "seats": oth_seats.reindex(oth.index, fill_value=0).values})
        res = pd.concat([named, others], ignore_index=True)
        res.insert(0, "election", e)
        lists.append(res)
        summaries.append(summ)
    results = pd.concat(lists, ignore_index=True)
    summary = pd.concat(summaries, ignore_index=True)
    return results, summary, pd.concat(named_lists, ignore_index=True)


def ep2024() -> pd.DataFrame:
    lst, _ = boe.parse_html(RAW / "BOE-A-2024-13092.xml", "EP2024")
    lst["label"] = [parties.label_for("EP2024", n, a) for n, a in zip(lst["list"], lst["abbr"],
                                                                       strict=True)]
    return lst.groupby(["code", "label"], as_index=False)["votes"].sum()


def constituencies_2026() -> pd.DataFrame:
    seats = boe.parse_decree_seats(RAW / "BOE-A-2026-20742.xml")
    electors = boe.parse_ine_electors(RAW / "INE-EG2026.pdf")
    df = seats.merge(electors, on="code")
    df.insert(1, "name", df["code"].map(NAME))
    df.insert(2, "ccaa", df["code"].map(CCAA))
    if df["seats"].sum() != 350 or len(df) != 52:
        raise ValueError("2026 constituencies: seats do not add up to 350")
    return df


def candidacies_2026() -> pd.DataFrame:
    cands = boe.parse_candidacies(RAW / "BOE-A-2026-23103.xml")
    cands = boe.apply_candidacy_corrections(cands, RAW / "BOE-A-2026-23383.xml")
    cands["label"] = [parties.label_for("2026", n, a) for n, a in zip(cands["name"],
                                                                      cands["abbr"], strict=True)]
    if sorted(cands["code"].unique()) != sorted(CODES):
        raise ValueError("2026 candidacies: constituencies missing")
    return cands


def poll_tables() -> tuple[pd.DataFrame, pd.DataFrame]:
    rows, results = [], []
    for e, page in POLL_PAGES.items():
        df, res = polls.parse_page(RAW / page, ELECTION_DATE[e], tables=2 if e == "2026" else 1)
        df = df.reset_index(names="poll")
        long = df.melt(id_vars=["poll", *polls.META], var_name="party",
                       value_name="share").dropna(subset=["share"])
        long.insert(0, "election", e)
        rows.append(long)
        results += [{"election": e, "party": k, "share": v} for k, v in res.items()]
    return pd.concat(rows, ignore_index=True), pd.DataFrame(results)


def population() -> dict:
    pop, when = boe.parse_ine_population(RAW / "INE-ECP3T26.pdf")
    return {"population": pop, "date": when,
            "source": "INE, Estadística Continua de Población (provisional)",
            "url": "https://www.ine.es/dyngs/Prensa/ECP3T26.pdf"}


def prepare() -> None:
    PROCESSED.mkdir(parents=True, exist_ok=True)
    results, summary, named = official_results()
    results.to_csv(PROCESSED / "results.csv", index=False)
    named.to_csv(PROCESSED / "list_results.csv", index=False)
    summary.to_csv(PROCESSED / "summary.csv", index=False)
    ep2024().to_csv(PROCESSED / "ep2024.csv", index=False)
    constituencies_2026().to_csv(PROCESSED / "constituencies_2026.csv", index=False)
    candidacies_2026().to_csv(PROCESSED / "candidacies_2026.csv", index=False)
    long, res = poll_tables()
    long.to_csv(PROCESSED / "polls.csv", index=False)
    res.to_csv(PROCESSED / "poll_results.csv", index=False)
    context = {"population": population(), "investitures": parties.INVESTITURES,
               "seats_2023": parties.SEATS_2023}
    (PROCESSED / "context.json").write_text(json.dumps(context, indent=2, ensure_ascii=False))
    for f in sorted(PROCESSED.iterdir()):
        print(f"  {f.name:32s} {f.stat().st_size:>9,d} B")
