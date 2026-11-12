"""National polls from the English Wikipedia lists, and the poll summary the model starts from.

The summary rule, used for 2026 and for every past election alike: take each polling firm's
latest poll whose fieldwork ended in the 14 days up to the cutoff, and the median across firms
of each party's share. No firm is excluded by hand; the CIS is one firm among the others and
is also reported against the median.
"""

from __future__ import annotations

import json
import re
import urllib.parse
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd
from lxml import etree
from lxml import html as lh

# Wikipedia article of each party column -> the key used here.
PARTY_KEYS = {
    "People's_Party_(Spain)": "PP",
    "Spanish_Socialist_Workers'_Party": "PSOE",
    "Vox_(political_party)": "VOX",
    "Citizens_(Spanish_political_party)": "CS",
    "Podemos_(Spanish_political_party)": "PODEMOS",
    "Unidos_Podemos": "UP",
    "Unidas_Podemos": "UP",
    "Sumar_(electoral_alliance)": "SUMAR",
    "Broad_Front_(Spain)": "FA",
    "Valencian_Front": "FV",
    "Popular_Unity_(Spain)": "IU",
    "Union,_Progress_and_Democracy": "UPYD",
    "Convergence_and_Union": "CIU",
    "Democratic_Convergence_of_Catalonia": "JUNTS",
    "Democracy_and_Freedom": "JUNTS",
    "Catalan_European_Democratic_Party": "PDECAT",
    "Together_for_Catalonia_(2017)": "JUNTS",
    "Together_for_Catalonia_(2020)": "JUNTS",
    "Republican_Left_of_Catalonia–Catalonia_Yes": "ERC",
    "Republican_Left_of_Catalonia–Sovereigntists": "ERC",
    "Republican_Left_of_Catalonia": "ERC",
    "Basque_Nationalist_Party": "PNV",
    "EH_Bildu": "BILDU",
    "Galician_Nationalist_Bloc": "BNG",
    "Canarian_Coalition": "CC",
    "Coalició_Compromís": "COMPROMIS",
    "Navarra_Suma": "NAS",
    "Navarrese_People's_Union": "UPN",
    "Regionalist_Party_of_Cantabria": "PRC",
    "Más_País": "MP",
    "Popular_Unity_Candidacy": "CUP",
    "Empty_Spain": "EV",
    "Animalist_Party_Against_Mistreatment_of_Animals": "PACMA",
    "Adelante_Andalucía_(2021)": "AA",
    "Se_Acabó_La_Fiesta": "SALF",
}

MONTHS = {m: i for i, m in enumerate(
    ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"], 1)}

WINDOW_DAYS = 14


def _text(el) -> str:
    return " ".join("".join(el.itertext()).replace("\xa0", " ").split())


def _share(cell) -> float:
    """The vote share: the cell's text before the line break (the seats come after it)."""
    raw = etree.tostring(cell, encoding="unicode")
    raw = re.split(r"<br\s*/?>", raw, maxsplit=1)[0]
    txt = _text(lh.fromstring(raw)) if raw.strip() else ""
    txt = re.sub(r"\[[^\]]*\]", "", txt)
    m = re.match(r"^\s*(\d+(?:\.\d+)?)\s*$", txt)
    return float(m.group(1)) if m else np.nan


def _firm(name: str) -> tuple[str, str, str]:
    """'CIS (Opina 360)[a][60]' -> firm 'CIS', label 'CIS (Opina 360)', commissioner ''.
    The firm is the name before any '/' or '(': one vote per firm in the median, so the
    re-estimates of the CIS's raw data by other firms count as the CIS."""
    name = re.sub(r"\[[^\]]*\]", "", name).strip()
    label, _, commissioner = name.partition("/")
    firm = label.split("(")[0].strip()
    return firm, label.strip(), commissioner.strip()


def _end_date(field: str, election: date) -> tuple[date | None, date | None]:
    """Fieldwork 'd Mon–d Mon', 'd–d Mon', 'd Mon' or with a year -> (start, end). The year,
    when missing, is the one that puts the end within the year before the election."""
    f = re.sub(r"\[[^\]]*\]", "", field).replace("—", "–").replace("-", "–").strip()
    parts = [p.strip() for p in f.split("–") if p.strip()]
    if not parts:
        return None, None

    def parse(p: str, default_month: int | None = None, default_year: int | None = None):
        m = re.match(r"^(\d{1,2})(?:\s+([A-Za-z]{3})[a-z]*)?(?:\s+(\d{4}))?$", p)
        if not m:
            return None
        d = int(m.group(1))
        mon = MONTHS.get(m.group(2).lower()) if m.group(2) else default_month
        yr = int(m.group(3)) if m.group(3) else default_year
        return d, mon, yr

    end = parse(parts[-1])
    if not end or not end[1]:
        return None, None
    d, mon, yr = end
    if yr is None:
        yr = election.year if (mon, d) <= (election.month, election.day) else election.year - 1
    end_d = date(yr, mon, d)
    start_d = None
    if len(parts) > 1:
        st = parse(parts[0], default_month=mon, default_year=None)
        if st and st[1]:
            sy = st[2] or (yr if (st[1], st[0]) <= (mon, d) else yr - 1)
            start_d = date(sy, st[1], st[0])
    return start_d, end_d


def parse_page(json_path: Path, election_date: str,
               tables: int = 1) -> tuple[pd.DataFrame, dict[str, float]]:
    """The polls of the first `tables` 'Voting intention estimates' tables (the pages split
    them by year, newest first, and write dates without the year) and the election-result row.

    A cell that spans several party columns (two lists polled together) is stored under the
    joined key, e.g. 'FA+FV'. A poll whose fieldwork is '?' right below another estimate from
    the same firm (the CIS publishes several estimates from one survey) takes its dates."""
    edate = date.fromisoformat(election_date)
    parsed = json.loads(Path(json_path).read_text())
    doc = lh.fromstring(parsed["parse"]["text"])
    found = []
    for tb in doc.xpath("//table[contains(@class,'wikitable')]"):
        heading = tb.xpath("preceding::*[self::h2 or self::h3 or self::h4][1]")
        if heading and "Voting intention" in heading[0].text_content():
            found.append(tb)
    frames, result = [], {}
    for tb in found[:tables]:
        df, res = _parse_table(tb, edate)
        frames.append(df)
        result = result or res
    df = pd.concat(frames, ignore_index=True)
    if len(df) and ((df["end"] > edate).any() or
                    (df["end"] < edate - timedelta(days=366)).any()):
        raise ValueError(f"{json_path}: fieldwork dates outside the year before the election")
    return df, result


def table_grid(table) -> list[list]:
    """The table as rows of cell elements, column by column: a cell spanning several columns
    or rows appears in each of them (the same element, so spans can be recognised)."""
    grid, pending = [], {}
    for tr in table.xpath(".//tr"):
        row = {}
        for col, (left, el) in list(pending.items()):
            row[col] = el
            if left == 1:
                del pending[col]
            else:
                pending[col] = (left - 1, el)
        col = 0
        for cell in tr.xpath("./th|./td"):
            while col in row:
                col += 1
            cs, rs = int(cell.get("colspan", 1)), int(cell.get("rowspan", 1))
            for k in range(cs):
                row[col + k] = cell
                if rs > 1:
                    pending[col + k] = (rs - 1, cell)
            col += cs
        grid.append([row.get(i) for i in range(max(row) + 1)] if row else [])
    return grid


def _parse_table(table, edate: date) -> tuple[pd.DataFrame, dict[str, float]]:
    grid = table_grid(table)
    cols: list[str] = []
    for th in grid[0]:
        links = th.xpath(".//a[@href]") if th is not None else []
        key = ""
        if links:
            art = urllib.parse.unquote(links[0].get("href").split("/wiki/")[-1])
            key = PARTY_KEYS.get(art, art)
        cols.append(key or (_text(th) if th is not None else ""))
    party_cols = list(range(4, len(cols) - 1))  # after firm, fieldwork, sample, turnout
    polls, result = [], {}
    for cells in grid[1:]:
        if len(cells) < 6 or any(c is None for c in cells[:3]) or cells[0].tag != "td":
            continue
        name = _text(cells[0])
        row, col = {}, 4
        while col < len(cols) - 1 and col < len(cells):
            cell, span = cells[col], 1
            while col + span < len(cells) and cells[col + span] is cell:
                span += 1
            if cell is not None:
                keys = [cols[i] for i in range(col, col + span) if i in party_cols]
                if keys:
                    row["+".join(keys)] = _share(cell)
            col += span
        start, end = _end_date(_text(cells[1]), edate)
        if "general election" in name.lower():
            if end == edate:  # the election itself, not the previous one listed below it
                result = {k: v for k, v in row.items() if not np.isnan(v)}
            continue
        firm, label, commissioner = _firm(name)
        if end is None:
            continue
        sample = re.sub(r"[^\d]", "", _text(cells[2]))
        polls.append({"firm": firm, "label": label, "commissioner": commissioner,
                      "start": start, "end": end,
                      "sample": int(sample) if sample else np.nan, **row})
    df = pd.DataFrame(polls)
    df = df.dropna(subset=party_columns(df), how="all")
    return df, result


META = ("firm", "label", "commissioner", "start", "end", "sample")


def party_columns(df: pd.DataFrame) -> list[str]:
    return [c for c in df.columns if c not in META]


def window(polls: pd.DataFrame, cutoff: date, days: int = WINDOW_DAYS) -> pd.DataFrame:
    """Each firm's latest poll with fieldwork ending in [cutoff - days, cutoff]."""
    inside = polls[(polls["end"] <= cutoff) & (polls["end"] >= cutoff - timedelta(days=days))]
    inside = inside.assign(_own=inside["label"] != inside["firm"])  # the firm's own first
    inside = inside.sort_values(["end", "_own"], ascending=[False, True], kind="stable")
    return inside.drop_duplicates("firm", keep="first").drop(columns="_own").reset_index(
        drop=True)


def median_shares(latest: pd.DataFrame, parties: list[str],
                  combos: dict[str, list[str]] | None = None) -> dict[str, float]:
    """Median across firms of each party's share (%). A combo (e.g. 'FA+FV') is the sum of its
    parts where a firm gives them apart, or the joint figure where it polls them together."""
    out = {}
    combos = combos or {}
    for party in parties:
        if party in combos:
            vals = []
            for _, r in latest.iterrows():
                parts = [r.get(p, np.nan) for p in combos[party]]
                joint = r.get(party, np.nan)
                if not np.isnan(joint):
                    vals.append(joint)
                elif all(not np.isnan(v) for v in parts):
                    vals.append(sum(parts))
            out[party] = float(np.median(vals)) if vals else np.nan
        else:
            vals = latest[party].dropna() if party in latest else pd.Series(dtype=float)
            out[party] = float(vals.median()) if len(vals) else np.nan
    return out


def count_reporting(latest: pd.DataFrame, party: str) -> int:
    return int(latest[party].notna().sum()) if party in latest else 0
