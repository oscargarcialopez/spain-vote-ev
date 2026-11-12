"""Every number the README, the carousel and the post may quote, formatted once from
results/summary.json, and a checker that flags any number in a text that is not one of them.

The carousel takes its numbers from here directly; prose written by hand is checked with
`voteev check FILE...`.
"""

from __future__ import annotations

import re
from datetime import date
from math import comb
from pathlib import Path

from . import theory
from .parties import DISPLAY

# Numbers that are not results: the law (176 of 350 seats, 52 constituencies, a 3%
# threshold, LOREG articles 69, 69.7 and 163, Constitution article 99.3 and its 48 hours), the
# design (14-day window, 1% floor, bandwidths, raking passes, the backtests' 20,000 runs and
# its targets), the inputs of the theory (b = 100 or 1,000 €), the carousel's format, the years
# cited, the days of the investiture votes (27 Sep and 16 Nov 2023, 7 Jan 2020) and of the
# election (29 Nov), the 7 January 2020 vote (167 yes, 165 no, 18 abstentions; Diario de
# Sesiones 14-PL-4), which is not in summary.json, and the +8.1 points of the "Neighbors"
# mailing in Gerber, Green and Larimer (2008).
CONSTANTS = {
    "176", "350", "52", "175", "69", "69.7", "163", "99", "99.3", "48",
    "14", "15", "0.01", "0.02", "0.05", "20,000", "75", "90", "80", "95",
    "100", "1,000", "1080", "1350", "7.5",
    "1951", "1954", "1957", "1965", "1968", "1973", "1975", "1983", "1990", "2007", "2008",
    "2012", "2015", "2016", "2018", "2019", "2020", "2023", "2024", "2026",
    "29", "27", "16",
    "167", "165", "18",
    "8.1",
}

MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August",
          "September", "October", "November", "December"]
LOTTERY = comb(49, 6)  # six numbers out of 49


def long_date(iso: str) -> str:
    d = date.fromisoformat(iso)
    return f"{d.day} {MONTHS[d.month - 1]} {d.year}"


def sig(x: float, digits: int = 2) -> str:
    """76,434 -> '76,000'; 10,765,236 -> '10.8 million'."""
    if x >= 1e9:
        return f"{x / 1e9:.1f} billion"
    if x >= 1e6:
        m = round(x / 1e6, 1)
        return f"{m:.0f} million" if m == int(m) and m >= 10 else f"{m:.1f} million"
    from math import floor, log10
    k = digits - 1 - floor(log10(abs(x)))
    return f"{round(x, k):,.0f}" if k <= 0 else f"{round(x, k):,.{k}f}"


def pct(x: float, digits: int = 0) -> str:
    return f"{100 * x:.{digits}f}%"


def signed(x: float, digits: int = 1) -> str:
    return f"{x:+.{digits}f}".replace("-", "−")


def euros(x: float) -> str:
    return f"{sig(x)} €"


def build(s: dict) -> dict[str, str]:
    f: dict[str, str] = {}
    meta, polls, vote = s["meta"], s["polls"], s["vote"]
    f["n"] = f"{meta['n']:,}"
    f["seed"] = str(meta["seed"])
    f["cutoff"] = long_date(polls["cutoff"])
    f["firms"] = str(polls["firms"])
    f["lead"] = str(polls["lead_days"])
    f["party_released"] = ", ".join(polls["party_released"]) or "none"
    for k, v in polls["medians"].items():
        f[f"poll.{k}"] = f"{v['median']:g}"
        f[f"poll.{k}.range"] = f"{v['min']:g}–{v['max']:g}"
        f[f"poll.{k}.firms"] = str(v["firms"])
    nat = vote["national"]
    for ev, v in nat.items():
        f[f"{ev}.one_in"] = sig(v["one_in"])
        f[f"{ev}.p"] = f"{v['p']:.1e}"
        f[f"{ev}.events"] = f"{v['events_counted']:,}"
        f[f"{ev}.rse"] = pct(v["mc_se"] / v["p"], 1)
        lo, hi = v["p"] - 1.96 * v["mc_se"], v["p"] + 1.96 * v["mc_se"]
        f[f"{ev}.ci"] = f"{sig(1 / hi)} – {sig(1 / lo)}"
        vals = list(v["by_bandwidth"].values())
        f[f"{ev}.bw_spread"] = pct(max(vals) / min(vals) - 1, 1)
    f["gse"] = sig(s["context"]["gse_2012_one_in"])
    f["lottery"] = sig(LOTTERY)
    f["lottery_exact"] = f"{LOTTERY:,}"
    f["lottery_def"] = "6 of 49"
    start = date.fromisoformat(polls["cutoff"]).toordinal() - polls["window_days"]
    f["window_start"] = long_date(date.fromordinal(start).isoformat())
    f["window"] = (f["window_start"].rsplit(" ", 1)[0] + " – " + f["cutoff"]
                   if f["window_start"][-4:] == f["cutoff"][-4:] else
                   f["window_start"] + " – " + f["cutoff"])
    f["ratio_gse"] = f"{s['context']['gse_2012_one_in'] / nat['majority_any']['one_in']:.0f}"
    prov = vote["provinces"]
    for ev in ("seat", "majority_any"):
        ranked = sorted(prov, key=lambda r: r[f"p_{ev}"], reverse=True)
        for k, r in enumerate(ranked[:3], start=1):
            f[f"{ev}.top{k}"] = r["name"]
            f[f"{ev}.top{k}.one_in"] = sig(r[f"one_in_{ev}"])
        for k, r in enumerate(ranked[::-1][:3], start=1):
            f[f"{ev}.bottom{k}"] = r["name"]
            f[f"{ev}.bottom{k}.one_in"] = sig(r[f"one_in_{ev}"])
        f[f"{ev}.spread"] = sig(ranked[-1][f"one_in_{ev}"] / ranked[0][f"one_in_{ev}"])
    for r in prov:
        key = r["name"]
        f[f"prov.{key}.seat"] = sig(r["one_in_seat"])
        f[f"prov.{key}.majority"] = sig(r["one_in_majority_any"])
        f[f"prov.{key}.eps"] = sig(r["electors_per_seat"])
        f[f"prov.{key}.seats"] = str(r["seats"])
        for b in ("F", "S", "S_no_JUNTS"):
            x = r[f"one_in_majority_{b}"]
            f[f"prov.{key}.{b}"] = sig(x) if x else "—"
    eps = sorted(prov, key=lambda r: r["electors_per_seat"])
    f["eps.min"], f["eps.min.name"] = sig(eps[0]["electors_per_seat"]), eps[0]["name"]
    f["eps.max"], f["eps.max.name"] = sig(eps[-1]["electors_per_seat"]), eps[-1]["name"]
    f["eps.ratio"] = f"{eps[-1]['electors_per_seat'] / eps[0]['electors_per_seat']:.1f}"
    for code, x in s["lists"].items():
        f[f"{code}.share"] = pct(x["share"], 1 if x["share"] >= 0.01 else 2)
        f[f"{code}.seats"] = f"{x['mean']:.0f}"
        f[f"{code}.i80"] = f"{x['lo80']}–{x['hi80']}"
        f[f"{code}.i95"] = f"{x['lo95']}–{x['hi95']}"
        f[f"{code}.p_seat"] = pct(x["p_any_seat"], 0 if x["p_any_seat"] >= 0.01 else 2)
        f[f"{code}.name"] = x["name"]
    for b, x in s["blocs"].items():
        f[f"bloc.{b}.mean"] = f"{x['mean']:.0f}"
        f[f"bloc.{b}.i80"] = f"{x['lo80']}–{x['hi80']}"
        f[f"bloc.{b}.i95"] = f"{x['lo95']}–{x['hi95']}"
        f[f"bloc.{b}.p"] = pct(x["p_majority"])
        f[f"bloc.{b}.p1"] = pct(x["p_majority"], 1)
        f[f"bloc.{b}.p_edge"] = pct(x["p_exactly_175_or_176"], 1)
    cal = s["calibration"]
    f["sigma_nat"] = f"{cal['sigma_national_logit']:.2f}"
    f["tau_ccaa"] = f"{cal['tau_ccaa']:.2f}"
    f["tau_prov"] = f"{cal['tau_province']:.2f}"
    f["sigma_tn"] = f"{cal['sigma_turnout_national_logit']:.2f}"
    f["sigma_tp"] = f"{cal['sigma_turnout_province_logit']:.2f}"
    f["n_poll_errors"] = str(cal["n_poll_errors"])
    f["n_residuals"] = f"{cal['n_provincial_residuals']:,}"
    pe = s["poll_errors"]
    big = [e for e in pe if e["actual"] >= 10]
    f["big_err_rms_pp"] = f"{(sum(e['error_pp'] ** 2 for e in big) / len(big)) ** 0.5:.1f}"
    f["big_err_max_pp"] = f"{max(abs(e['error_pp']) for e in big):.1f}"
    bt = s["backtest"]
    tried = next(t for t in bt["tried"] if t["factor"] == bt["chosen_factor"])
    f["bt.lists"] = str(tried["lists"])
    f["bt.in80"] = f"{tried['in80']} of {tried['lists']}"
    f["bt.in95"] = f"{tried['in95']} of {tried['lists']}"
    f["bt.cov80"] = pct(tried["cov80"])
    f["bt.cov95"] = pct(tried["cov95"])
    f["bt.factor"] = f"{bt['chosen_factor']:.2f}"
    lead = bt["at_2026_lead"]
    f["bt_lead.in80"] = f"{lead['in80']} of {lead['lists']}"
    f["bt_lead.in95"] = f"{lead['in95']} of {lead['lists']}"
    for run in bt["runs"]:
        e = run["election"]
        f[f"bt.{e}.cutoff"] = long_date(run["cutoff"])
        f[f"bt.{e}.firms"] = str(run["firms"])
        for x in run["lists"]:
            f[f"bt.{e}.{x['list']}"] = f"{x['actual']} in {x['lo80']}–{x['hi80']}"
            f[f"bt.{e}.{x['list']}.i95"] = f"{x['lo95']}–{x['hi95']}"
        misses = [x for x in run["lists"] if x["counted"] and not x["in80"]]
        f[f"bt.{e}.misses80"] = ", ".join(
            f"{DISPLAY.get(x['list'], x['list'])} ({x['actual']} vs {x['lo80']}–{x['hi80']})"
            for x in misses) or "none"
        for b in run["blocs"]:
            f[f"bt.{e}.{b['bloc']}.p"] = pct(b["p_majority"])
            f[f"bt.{e}.{b['bloc']}.actual"] = str(b["actual"])
            f[f"bt.{e}.{b['bloc']}.pctile"] = pct(b["actual_percentile"])
            f[f"bt.{e}.{b['bloc']}.i80"] = f"{b['lo80']}–{b['hi80']}"
    pw = s["power"]
    for p, x in pw["congress_2023"].items():
        f[f"pw23.{p}.seats"] = pct(x["seat_share"], 1)
        f[f"pw23.{p}.ss"] = pct(x["shapley_shubik"], 1)
        f[f"pw23.{p}.bz"] = pct(x["banzhaf"], 1)
    for p, x in pw["simulated"].items():
        f[f"pw.{p}.seats"] = pct(x["seat_share"], 1)
        f[f"pw.{p}.ss"] = pct(x["shapley_shubik"], 1)
        f[f"pw.{p}.bz"] = pct(x["banzhaf"], 1)
    f["pw.sample"] = f"{pw['sample']:,}"
    th = s["theory"]
    f["cost"] = f"{th['cost']:.0f} €"
    f["population"] = sig(th["population"], 3)
    f["population_exact"] = f"{th['population']:,}"
    f["population_date"] = s["context"]["population"]["date"]
    for k in ("seat", "majority"):
        x = th[k]
        f[f"th.{k}.B"] = euros(x["break_even_benefit"])
        f[f"th.{k}.pN"] = f"{x['p_times_n']:.1f}" if x["p_times_n"] < 100 else sig(x["p_times_n"])
        f[f"th.{k}.alpha100"] = pct(x["alpha_for_b_100"], 1 if x["alpha_for_b_100"] > 0.001
                                    else 3)
        f[f"th.{k}.alpha1000"] = pct(x["alpha_for_b_1000"], 2 if x["alpha_for_b_1000"] > 1e-4
                                     else 4)
        f[f"th.{k}.inv_alpha100"] = f"{1 / x['alpha_for_b_100']:,.0f}"
        for inf in x["influence"]:
            f[f"th.{k}.infl{inf['votes_per_hour']}"] = euros(inf["break_even_benefit"])
    f["vph_lo"], f["vph_hi"] = (str(v) for v in th["votes_per_hour"])
    cis = s.get("cis")
    if cis:
        f["cis.end"] = long_date(cis["end"])
        f["cis.others"] = str(cis["others"])
        for p, x in cis["lists"].items():
            f[f"cis.{p}"] = f"{x['cis']:.1f}"
            f[f"cis.{p}.others"] = f"{x['others_median']:.1f}"
            f[f"cis.{p}.diff"] = signed(x["difference"])
    sens = s.get("sensitivity_party_polls")
    if sens:
        f["sens.excluded"] = ", ".join(sens["excluded"])
        for b, p in sens["blocs"].items():
            f[f"sens.{b}.p"] = pct(p, 1)
    f["minutes"] = str(theory.MINUTES)
    f["value_of_time"] = f"{theory.VALUE_OF_TIME:.0f} €/h"
    ctx = s["context"]
    for who, inv in ctx["investitures"].items():
        f[f"inv.{who}.yes"], f[f"inv.{who}.no"] = str(inv["yes"]), str(inv["no"])
        for p, k in inv["yes_by_party"].items():
            f[f"inv.{who}.{p}"] = str(k)
    for p, k in ctx["seats_2023"].items():
        f[f"seats23.{p}"] = str(k)
    f["n_backtest"] = f"{s['backtest']['rule']['n']:,}"
    return f


NUMBER = re.compile(r"(?<![\w.])[+\-−]?(\d{1,3}(?:,\d{3})+|\d+)(\.\d+)?%?")


def numbers_in(text: str) -> list[str]:
    """Numeric tokens, without sign, percent or thousands separators. Code spans and blocks,
    links, ISO dates, versions, table-of-contents digits and a trailing References section
    are not claims."""
    text = re.split(r"^#+ References\s*$", text, flags=re.M)[0]
    text = re.sub(r"^```.*?^```", " ", text, flags=re.S | re.M)
    text = re.sub(r"`[^`\n]*`", " ", text)
    text = re.sub(r"(?<![\d,.])(\d+),(\d{1,2})(?!\d)", r"\1.\2", text)  # 84,2 (Spanish)
    text = re.sub(r"\(https?://[^)]*\)|https?://\S+|github\.com/\S+", " ", text)
    text = re.sub(r"\b\d{4}-\d{2}-\d{2}\b", " ", text)
    text = re.sub(r"BOE-A-\d{4}-\d+|DSCD-[\w-]+|SHA-256", " ", text)
    text = re.sub(r"\b\d+\.\d+\.\d+\b", " ", text)
    return [(m.group(1) + (m.group(2) or "")).replace(",", "") for m in NUMBER.finditer(text)]


def allowed(facts: dict[str, str]) -> set[str]:
    ok = {n for v in facts.values() for n in numbers_in(v)}
    ok |= {c.replace(",", "") for c in CONSTANTS}
    ok |= {str(i) for i in range(11)}
    return ok


def check(text: str, facts: dict[str, str]) -> list[str]:
    ok = allowed(facts)
    return sorted({n for n in numbers_in(text) if n not in ok}, key=float)


def check_files(paths: list[Path], summary: dict) -> int:
    facts = build(summary)
    bad = 0
    for path in paths:
        text = Path(path).read_text()
        missing = check(text, facts)
        status = "ok" if not missing else "NOT IN RESULTS: " + ", ".join(missing)
        print(f"{path}: {len(numbers_in(text))} numbers; {status}")
        bad += len(missing)
    return bad
