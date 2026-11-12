"""Every number the README, the carousel and the post may quote, formatted once from
results/summary.json, in English or in Spanish, and a checker that flags any number in a text
that is not one of them.

English: 76,000 · 10.8 million · 94.2% · 5 € · 29 November 2026.
Spanish (Spain): 76.000 · 10,8 millones · 94,2 % · 5 € · 29 de noviembre de 2026, with a
no-break space before % and €, a period for thousands from 1.000 up (never in years) and a
decimal comma.

The carousel takes its numbers from here directly; prose written by hand is checked with
`voteev check`. A text can switch language midway with a line `<!-- lang: en -->` or
`<!-- lang: es -->`.
"""

from __future__ import annotations

import re
from datetime import date
from math import comb, floor, log10
from pathlib import Path

from . import legibility, theory
from .parties import DISPLAY

LANGS = ("en", "es")
NBSP = " "

# Numbers that are not results: the law (176 of 350 seats, 52 constituencies, a 3%
# threshold, LOREG articles 69, 69.7 and 163, Constitution article 99.3 and its 48 hours), the
# design (14-day window, 1% floor, bandwidths, raking passes, the backtests' 20,000 runs and
# its targets), the inputs of the theory (b = 100 or 1,000 €), the carousel's format, the years
# cited, the days of the investiture votes (27 Sep and 16 Nov 2023, 7 Jan 2020) and of the
# election (29 Nov), the 7 January 2020 vote (167 yes, 165 no, 18 abstentions; Diario de
# Sesiones 14-PL-4), which is not in summary.json, and the +8.1 points of the "Neighbors"
# mailing in Gerber, Green and Larimer (2008). Written in English form; compared canonically.
CONSTANTS = {
    "176", "350", "52", "175", "69", "69.7", "163", "99", "99.3", "48",
    "14", "15", "0.01", "0.02", "0.05", "20,000", "75", "90", "80", "95",
    "100", "1,000", "1080", "1350", "7.5",
    "1951", "1954", "1957", "1965", "1968", "1973", "1975", "1983", "1990", "2007", "2008",
    "2011", "2012", "2015", "2016", "2018", "2019", "2020", "2023", "2024", "2026",
    "29", "27", "16",
    "167", "165", "18",
    "8.1",
}

MONTHS = {
    "en": ["January", "February", "March", "April", "May", "June", "July", "August",
           "September", "October", "November", "December"],
    "es": ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto",
           "septiembre", "octubre", "noviembre", "diciembre"],
}
LOTTERY = comb(49, 6)  # six numbers out of 49 (La Primitiva)


class Fmt:
    """Number and date formatting for one language."""

    def __init__(self, lang: str = "en"):
        if lang not in LANGS:
            raise ValueError(f"unknown language {lang!r}")
        self.lang = lang
        self.es = lang == "es"

    def _local(self, s: str) -> str:
        """English separators to Spanish ones: 1,234.5 -> 1.234,5."""
        if not self.es:
            return s
        return s.replace(",", "\x00").replace(".", ",").replace("\x00", ".")

    def num(self, x: float, digits: int = 0) -> str:
        """Fixed decimals with thousands separators: 76,000 / 76.000; 4.6 / 4,6."""
        return self._local(f"{x:,.{digits}f}")

    def g(self, x: float) -> str:
        """Shortest form, no thousands separator: 26.15 / 26,15."""
        return self._local(f"{x:g}")

    def sig(self, x: float, digits: int = 2) -> str:
        """76,434 -> 76,000 / 76.000; 10,765,236 -> 10.8 million / 10,8 millones."""
        if x >= 1e9:
            if not self.es:
                return f"{x / 1e9:.1f} billion"
            m = x / 1e6  # Spanish counts thousands of millions: 1.100 millones
            k = digits - 1 - floor(log10(m))
            return f"{self.num(round(m, k))} millones"
        if x >= 1e6:
            m = round(x / 1e6, 1)
            text = f"{m:.0f}" if m == int(m) and m >= 10 else f"{m:.1f}"
            return f"{self._local(text)} {'millones' if self.es else 'million'}"
        k = digits - 1 - floor(log10(abs(x)))
        return self.num(round(x, k), max(k, 0))

    def pct(self, x: float, digits: int = 0) -> str:
        return f"{self.num(100 * x, digits)}{NBSP}%" if self.es else f"{100 * x:.{digits}f}%"

    def signed(self, x: float, digits: int = 1) -> str:
        return self._local(f"{x:+.{digits}f}").replace("-", "−")

    def euros(self, x: float) -> str:
        if self.es:
            return f"{self.sig(x)} de euros" if x >= 1e6 else f"{self.sig(x)}{NBSP}€"
        return f"{self.sig(x)} €"

    def date(self, iso: str) -> str:
        d = date.fromisoformat(iso)
        month = MONTHS[self.lang][d.month - 1]
        return f"{d.day} de {month} de {d.year}" if self.es else f"{d.day} {month} {d.year}"

    def period(self, start: str, end: str) -> str:
        """27 October – 10 November 2026 / del 27 de octubre al 10 de noviembre de 2026."""
        a, b = date.fromisoformat(start), date.fromisoformat(end)
        if self.es:
            first = (f"{a.day} de {MONTHS['es'][a.month - 1]}" if a.year == b.year
                     else self.date(start))
            return f"del {first} al {self.date(end)}"
        first = f"{a.day} {MONTHS['en'][a.month - 1]}" if a.year == b.year else self.date(start)
        return f"{first} – {self.date(end)}"

    def between(self, start: str, end: str) -> str:
        """27 October – 10 November 2026 / entre el 27 de octubre y el 10 de noviembre de 2026."""
        if not self.es:
            return self.period(start, end)
        return self.period(start, end).replace("del ", "entre el ", 1).replace(" al ", " y el ", 1)

    def of(self, a: int, b: int) -> str:
        return f"{a} {'de' if self.es else 'of'} {b}"

    def word(self, en: str, es: str) -> str:
        return es if self.es else en


def long_date(iso: str) -> str:
    return Fmt("en").date(iso)


def sig(x: float, digits: int = 2) -> str:
    return Fmt("en").sig(x, digits)


def pct(x: float, digits: int = 0) -> str:
    return Fmt("en").pct(x, digits)


def _government_facts(f: dict[str, str], fm: Fmt, prefix: str, g: dict) -> None:
    """Who is invested (summary["government"] and its variants)."""
    for cand, x in g["candidates"].items():
        f[f"{prefix}.{cand}.p"] = fm.pct(x["p"])
        f[f"{prefix}.{cand}.p1"] = fm.pct(x["p"], 1)
        f[f"{prefix}.{cand}.first"] = fm.pct(x["first_vote"], 1)
        f[f"{prefix}.{cand}.second"] = fm.pct(x["second_vote"], 1)
        if "yes_mean" in x:
            f[f"{prefix}.{cand}.yes"] = fm.num(x["yes_mean"])
            f[f"{prefix}.{cand}.yes80"] = f"{x['yes_lo80']}–{x['yes_hi80']}"
    f[f"{prefix}.blocked"] = fm.pct(g["blocked"], 1)
    f[f"{prefix}.second"] = fm.pct(g["second_vote"], 1)
    f[f"{prefix}.both"] = fm.pct(g["both_possible"], 2)


def build(s: dict, lang: str = "en") -> dict[str, str]:
    fm = Fmt(lang)
    f: dict[str, str] = {}
    meta, polls, vote = s["meta"], s["polls"], s["vote"]
    f["n"] = fm.num(meta["n"])
    f["seed"] = str(meta["seed"])
    f["cutoff"] = fm.date(polls["cutoff"])
    f["firms"] = str(polls["firms"])
    f["lead"] = str(polls["lead_days"])
    f["party_released"] = ", ".join(polls["party_released"]) or fm.word("none", "ninguna")
    for k, v in polls["medians"].items():
        f[f"poll.{k}"] = fm.g(v["median"])
        f[f"poll.{k}.range"] = f"{fm.g(v['min'])}–{fm.g(v['max'])}"
        f[f"poll.{k}.firms"] = str(v["firms"])
    nat = vote["national"]
    for ev, v in nat.items():
        f[f"{ev}.one_in"] = fm.sig(v["one_in"])
        f[f"{ev}.p"] = fm._local(f"{v['p']:.1e}")
        f[f"{ev}.events"] = fm.num(v["events_counted"])
        f[f"{ev}.rse"] = fm.pct(v["mc_se"] / v["p"], 1)
        lo, hi = v["p"] - 1.96 * v["mc_se"], v["p"] + 1.96 * v["mc_se"]
        f[f"{ev}.ci"] = f"{fm.sig(1 / hi)} – {fm.sig(1 / lo)}"
        vals = list(v["by_bandwidth"].values())
        f[f"{ev}.bw_spread"] = fm.pct(max(vals) / min(vals) - 1, 1)
    f["gse"] = fm.sig(s["context"]["gse_2012_one_in"])
    f["lottery"] = fm.sig(LOTTERY)
    f["lottery_exact"] = fm.num(LOTTERY)
    f["lottery_def"] = fm.of(6, 49)
    start = date.fromisoformat(polls["cutoff"]).toordinal() - polls["window_days"]
    start_iso = date.fromordinal(start).isoformat()
    f["window_start"] = fm.date(start_iso)
    f["window"] = fm.period(start_iso, polls["cutoff"])
    f["window_between"] = fm.between(start_iso, polls["cutoff"])
    f["ratio_gse"] = f"{s['context']['gse_2012_one_in'] / nat['majority_any']['one_in']:.0f}"
    if "government" in nat:
        f["ratio_gse_gov"] = f"{s['context']['gse_2012_one_in'] / nat['government']['one_in']:.0f}"
    prov = vote["provinces"]
    for ev in [e for e in ("seat", "majority_any", "government") if f"p_{e}" in prov[0]]:
        ranked = sorted(prov, key=lambda r: r[f"p_{ev}"], reverse=True)
        for k, r in enumerate(ranked[:3], start=1):
            f[f"{ev}.top{k}"] = r["name"]
            f[f"{ev}.top{k}.one_in"] = fm.sig(r[f"one_in_{ev}"])
        for k, r in enumerate(ranked[::-1][:3], start=1):
            f[f"{ev}.bottom{k}"] = r["name"]
            f[f"{ev}.bottom{k}.one_in"] = fm.sig(r[f"one_in_{ev}"])
        f[f"{ev}.spread"] = fm.sig(ranked[-1][f"one_in_{ev}"] / ranked[0][f"one_in_{ev}"])
    for r in prov:
        key = r["name"]
        f[f"prov.{key}.seat"] = fm.sig(r["one_in_seat"])
        f[f"prov.{key}.majority"] = fm.sig(r["one_in_majority_any"])
        if r.get("one_in_government"):
            f[f"prov.{key}.government"] = fm.sig(r["one_in_government"])
        f[f"prov.{key}.eps"] = fm.sig(r["electors_per_seat"])
        f[f"prov.{key}.seats"] = str(r["seats"])
        for b in ("F", "S", "S_no_JUNTS"):
            x = r[f"one_in_majority_{b}"]
            f[f"prov.{key}.{b}"] = fm.sig(x) if x else "—"
    eps = sorted(prov, key=lambda r: r["electors_per_seat"])
    f["eps.min"], f["eps.min.name"] = fm.sig(eps[0]["electors_per_seat"]), eps[0]["name"]
    f["eps.max"], f["eps.max.name"] = fm.sig(eps[-1]["electors_per_seat"]), eps[-1]["name"]
    f["eps.ratio"] = fm.num(eps[-1]["electors_per_seat"] / eps[0]["electors_per_seat"], 1)
    for code, x in s["lists"].items():
        f[f"{code}.share"] = fm.pct(x["share"], 1 if x["share"] >= 0.01 else 2)
        f[f"{code}.seats"] = fm.num(x["mean"])
        f[f"{code}.i80"] = f"{x['lo80']}–{x['hi80']}"
        f[f"{code}.i95"] = f"{x['lo95']}–{x['hi95']}"
        f[f"{code}.p_seat"] = fm.pct(x["p_any_seat"], 0 if x["p_any_seat"] >= 0.01 else 2)
        f[f"{code}.name"] = x["name"]
    for b, x in s["blocs"].items():
        f[f"bloc.{b}.mean"] = fm.num(x["mean"])
        f[f"bloc.{b}.i80"] = f"{x['lo80']}–{x['hi80']}"
        f[f"bloc.{b}.i95"] = f"{x['lo95']}–{x['hi95']}"
        f[f"bloc.{b}.p"] = fm.pct(x["p_majority"])
        f[f"bloc.{b}.p1"] = fm.pct(x["p_majority"], 1)
        f[f"bloc.{b}.p_edge"] = fm.pct(x["p_exactly_175_or_176"], 1)
    gv = s.get("government")
    if gv:
        _government_facts(f, fm, "gov", gv)
        for name, g in gv.get("variants", {}).items():
            _government_facts(f, fm, f"gov.{name}", g)
        for lab, k in gv["keys"].items():
            for cand in ("PP", "PSOE", "any"):
                f[f"key.{lab}.{cand}"] = fm.pct(k[cand], 1 if k[cand] < 0.1 else 0)
    cal = s["calibration"]
    f["sigma_nat"] = fm.num(cal["sigma_national_logit"], 2)
    f["tau_ccaa"] = fm.num(cal["tau_ccaa"], 2)
    f["tau_prov"] = fm.num(cal["tau_province"], 2)
    f["sigma_tn"] = fm.num(cal["sigma_turnout_national_logit"], 2)
    f["sigma_tp"] = fm.num(cal["sigma_turnout_province_logit"], 2)
    f["n_poll_errors"] = str(cal["n_poll_errors"])
    f["n_residuals"] = fm.num(cal["n_provincial_residuals"])
    pe = s["poll_errors"]
    big = [e for e in pe if e["actual"] >= 10]
    f["big_err_rms_pp"] = fm.num((sum(e["error_pp"] ** 2 for e in big) / len(big)) ** 0.5, 1)
    f["big_err_max_pp"] = fm.num(max(abs(e["error_pp"]) for e in big), 1)
    bt = s["backtest"]
    tried = next(t for t in bt["tried"] if t["factor"] == bt["chosen_factor"])
    f["bt.lists"] = str(tried["lists"])
    f["bt.in80"] = fm.of(tried["in80"], tried["lists"])
    f["bt.in95"] = fm.of(tried["in95"], tried["lists"])
    f["bt.cov80"] = fm.pct(tried["cov80"])
    f["bt.cov95"] = fm.pct(tried["cov95"])
    f["bt.factor"] = fm.num(bt["chosen_factor"], 2)
    lead = bt["at_2026_lead"]
    f["bt_lead.in80"] = fm.of(lead["in80"], lead["lists"])
    f["bt_lead.in95"] = fm.of(lead["in95"], lead["lists"])
    vs = fm.word("vs", "frente a")
    for run in bt["runs"]:
        e = run["election"]
        f[f"bt.{e}.cutoff"] = fm.date(run["cutoff"])
        f[f"bt.{e}.firms"] = str(run["firms"])
        for x in run["lists"]:
            f[f"bt.{e}.{x['list']}"] = (f"{x['actual']} {fm.word('in', 'en')} "
                                        f"{x['lo80']}–{x['hi80']}")
            f[f"bt.{e}.{x['list']}.i95"] = f"{x['lo95']}–{x['hi95']}"
        misses = [x for x in run["lists"] if x["counted"] and not x["in80"]]
        f[f"bt.{e}.misses80"] = ", ".join(
            f"{DISPLAY.get(x['list'], x['list'])} ({x['actual']} {vs} {x['lo80']}–{x['hi80']})"
            for x in misses) or fm.word("none", "ninguno")
        for b in run["blocs"]:
            f[f"bt.{e}.{b['bloc']}.p"] = fm.pct(b["p_majority"])
            f[f"bt.{e}.{b['bloc']}.actual"] = str(b["actual"])
            f[f"bt.{e}.{b['bloc']}.pctile"] = fm.pct(b["actual_percentile"])
            f[f"bt.{e}.{b['bloc']}.i80"] = f"{b['lo80']}–{b['hi80']}"
    pw = s["power"]
    for p, x in pw["congress_2023"].items():
        f[f"pw23.{p}.seats"] = fm.pct(x["seat_share"], 1)
        f[f"pw23.{p}.ss"] = fm.pct(x["shapley_shubik"], 1)
        f[f"pw23.{p}.bz"] = fm.pct(x["banzhaf"], 1)
    for p, x in pw["simulated"].items():
        f[f"pw.{p}.seats"] = fm.pct(x["seat_share"], 1)
        f[f"pw.{p}.ss"] = fm.pct(x["shapley_shubik"], 1)
        f[f"pw.{p}.bz"] = fm.pct(x["banzhaf"], 1)
    f["pw.sample"] = fm.num(pw["sample"])
    th = s["theory"]
    f["cost"] = f"{fm.num(th['cost'])}{NBSP if fm.es else ' '}€"
    f["population"] = fm.sig(th["population"], 3)
    f["population_exact"] = fm.num(th["population"])
    f["population_date"] = s["context"]["population"]["date"]
    for k in [k for k in ("seat", "majority", "government") if k in th]:
        x = th[k]
        f[f"th.{k}.B"] = fm.euros(x["break_even_benefit"])
        f[f"th.{k}.pN"] = (fm.num(x["p_times_n"], 1) if x["p_times_n"] < 100
                           else fm.sig(x["p_times_n"]))
        f[f"th.{k}.alpha100"] = fm.pct(x["alpha_for_b_100"],
                                       1 if x["alpha_for_b_100"] > 0.001 else 3)
        f[f"th.{k}.alpha1000"] = fm.pct(x["alpha_for_b_1000"],
                                        2 if x["alpha_for_b_1000"] > 1e-4 else 4)
        f[f"th.{k}.inv_alpha100"] = fm.num(1 / x["alpha_for_b_100"])
        for inf in x["influence"]:
            f[f"th.{k}.infl{inf['votes_per_hour']}"] = fm.euros(inf["break_even_benefit"])
    f["vph_lo"], f["vph_hi"] = (fm.g(v) if fm.es else str(v) for v in th["votes_per_hour"])
    cis = s.get("cis")
    if cis:
        f["cis.end"] = fm.date(cis["end"])
        f["cis.others"] = str(cis["others"])
        for p, x in cis["lists"].items():
            f[f"cis.{p}"] = fm.num(x["cis"], 1)
            f[f"cis.{p}.others"] = fm.num(x["others_median"], 1)
            f[f"cis.{p}.diff"] = fm.signed(x["difference"])
    sens = s.get("sensitivity_party_polls")
    if sens:
        f["sens.excluded"] = ", ".join(sens["excluded"])
        for b, p in sens["blocs"].items():
            f[f"sens.{b}.p"] = fm.pct(p, 1)
    f["minutes"] = str(theory.MINUTES)
    f["value_of_time"] = (f"{fm.num(theory.VALUE_OF_TIME)}{NBSP}€/h" if fm.es
                          else f"{theory.VALUE_OF_TIME:.0f} €/h")
    ctx = s["context"]
    for who, inv in ctx["investitures"].items():
        f[f"inv.{who}.yes"], f[f"inv.{who}.no"] = str(inv["yes"]), str(inv["no"])
        for p, k in inv["yes_by_party"].items():
            f[f"inv.{who}.{p}"] = str(k)
    for p, k in ctx["seats_2023"].items():
        f[f"seats23.{p}"] = str(k)
    f["n_backtest"] = fm.num(s["backtest"]["rule"]["n"])
    # The type floor of the carousel: a criterion, not a result (legibility.py).
    lg = legibility.facts()
    f["type.angle"] = fm.num(lg["angle"], 2)
    f["type.cps_low"] = fm.num(lg["cps_low"], 2)
    f["type.cps_high"] = fm.num(lg["cps_high"], 1)
    f["type.distance_mm"] = fm.num(lg["distance_mm"])
    f["type.phone_in"] = fm.num(lg["phone_in"], 1)
    f["type.screen_mm"] = fm.num(lg["screen_mm"], 1)
    f["type.screen_px"] = fm.num(lg["screen_px"])
    f["type.screen_ppi"] = fm.num(lg["screen_ppi"])
    for style in ("regular", "italic"):
        f[f"type.xh_{style}"] = fm.num(lg[f"xh_{style}"], 3)
        f[f"type.raw_{style}"] = fm.num(lg[f"raw_{style}"], 2)
        f[f"type.min_{style}"] = fm.num(lg[f"min_{style}"], 1)
    f["type.px_per_pt"] = fm.num(lg["px_per_pt"], 1)
    return f


# --- reading numbers back ---------------------------------------------------------------------

RUN = re.compile(r"(?<![\w.,])\d(?:[\d.,]*\d)?")
VALID = {
    "en": re.compile(r"\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+(?:\.\d+)?"),
    "es": re.compile(r"\d{1,3}(?:\.\d{3})+(?:,\d+)?|\d+(?:,\d+)?"),
}
LANG_MARK = re.compile(r"^<!-- lang: (en|es) -->\s*$", re.M)


def _clean(text: str) -> str:
    """Drop what is not a numeric claim: a trailing References section, code, links, ISO
    dates, document identifiers, versions and article numbers (art. 69.7, art. 99.3)."""
    text = re.split(r"^#+ (?:References|Referencias)\s*$", text, flags=re.M)[0]
    text = re.sub(r"^```.*?^```", " ", text, flags=re.S | re.M)
    text = re.sub(r"`[^`\n]*`", " ", text)
    text = re.sub(r"\(https?://[^)]*\)|https?://\S+|github\.com/\S+", " ", text)
    text = re.sub(r"\b\d{4}-\d{2}-\d{2}\b", " ", text)
    text = re.sub(r"BOE-A-\d{4}-\d+|DSCD-[\w-]+|SHA-256", " ", text)
    text = re.sub(r"\b\d+\.\d+\.\d+\b", " ", text)
    return re.sub(r"\b(?:art\.|article|artículo)\s*\d+(?:\.\d+)?", " ", text, flags=re.I)


def _canonical(run: str, lang: str) -> str:
    """76.000 (es) or 76,000 (en) -> '76000'; 10,8 (es) or 10.8 (en) -> '10.8'."""
    if lang == "es":
        return run.replace(".", "").replace(",", ".")
    return run.replace(",", "")


def _scan(text: str, lang: str) -> tuple[list[str], list[str]]:
    """Canonical numbers and formatting problems in a text written in one language."""
    text = _clean(text)
    nums, bad = [], []
    for m in RUN.finditer(text):
        run = m.group()
        if not VALID[lang].fullmatch(run):
            bad.append(f"{run} (not {lang} number format)")
            continue
        nums.append(_canonical(run, lang))
        plain_long = run.isdigit() and len(run) >= (4 if lang == "es" else 5)
        if plain_long and not (lang == "es" and 1900 <= int(run) <= 2099):
            bad.append(f"{run} (needs a thousands separator)")
    if lang == "es":
        for m in re.finditer(r"\d(?:[\d.,]*\d)? ?([%€])", text):
            bad.append(f"{m.group()} (no-break space before {m.group(1)})")
    return nums, bad


def segments(text: str, lang: str) -> list[tuple[str, str]]:
    """Split a text at `<!-- lang: xx -->` lines: (language, part) pairs."""
    out, pos = [], 0
    for m in LANG_MARK.finditer(text):
        out.append((lang, text[pos:m.start()]))
        lang, pos = m.group(1), m.end()
    out.append((lang, text[pos:]))
    return [(lg, part) for lg, part in out if part.strip()]


def numbers_in(text: str, lang: str = "en") -> list[str]:
    """Numeric tokens, canonical (no thousands separator, '.' for decimals)."""
    return _scan(text, lang)[0]


def allowed(facts: dict[str, str], lang: str = "en") -> set[str]:
    ok = {n for v in facts.values() for n in numbers_in(v, lang)}
    ok |= {c.replace(",", "") for c in CONSTANTS}
    ok |= {str(i) for i in range(11)}
    return ok


def check(text: str, facts: dict[str, str], lang: str = "en") -> list[str]:
    """Numbers in a one-language text that are not in the facts (sorted), then formatting
    problems."""
    nums, bad = _scan(text, lang)
    ok = allowed(facts, lang)
    return sorted({n for n in nums if n not in ok}, key=float) + bad


def check_text(text: str, summary: dict, lang: str = "en",
               cache: dict[str, dict] | None = None) -> tuple[int, list[str]]:
    cache = {} if cache is None else cache
    count, problems = 0, []
    for lg, part in segments(text, lang):
        if lg not in cache:
            cache[lg] = build(summary, lg)
        count += len(numbers_in(part, lg))
        problems += [f"[{lg}] {p}" for p in check(part, cache[lg], lg)]
    return count, problems


def check_files(paths: list[Path] | list[tuple[Path, str]], summary: dict) -> int:
    """Each path, or (path, language); English by default. Prints one line per file and
    returns the number of problems."""
    cache: dict[str, dict] = {}
    bad = 0
    for item in paths:
        path, lang = item if isinstance(item, tuple) else (item, "en")
        count, problems = check_text(Path(path).read_text(), summary, lang, cache)
        status = "ok" if not problems else "PROBLEMS: " + "; ".join(problems)
        print(f"{path} ({lang}): {count} numbers; {status}")
        bad += len(problems)
    return bad
