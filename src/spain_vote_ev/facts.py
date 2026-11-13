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

from . import theory
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
    "2011", "2012", "2013", "2015", "2016", "2018", "2019", "2020", "2021", "2023", "2024",
    "2026",
    "29", "27", "16",
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
        """76,434 -> 76,000 / 76.000; 10,765,236 -> 10.8 million / 10,8 millones;
        457,312,000 -> 457 million (no more than three digits in front of "million")."""
        if x >= 999.5e6:
            if not self.es:
                return f"{x / 1e9:.1f} billion"
            m = x / 1e6  # Spanish counts thousands of millions: 1.100 millones
            k = digits - 1 - floor(log10(m))
            return f"{self.num(round(m, k))} millones"
        if x >= 1e6:
            m = x / 1e6
            if m >= 99.95:
                text = f"{m:.0f}"
            else:
                m = round(m, 1)
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

    def join(self, items: list[str]) -> str:
        """'a, b and c' / 'a, b y c'."""
        items = list(items)
        if len(items) < 2:
            return "".join(items)
        return ", ".join(items[:-1]) + (" y " if self.es else " and ") + items[-1]

    def month(self, iso: str) -> str:
        """October 2016 / octubre de 2016."""
        d = date.fromisoformat(iso)
        return f"{MONTHS[self.lang][d.month - 1]}{' de' if self.es else ''} {d.year}"


# The groups of the investiture record (data/curated/investitures.csv), shortened for tables.
RECORD_NAMES = {"CDC (PDeCAT)": "PDeCAT", "DL (CDC)": "DL", "Navarra Suma (NA+)": "NA+",
                "IU-UP (Unidad Popular)": "IU-UP",
                "En Común-Unidas Podemos (Galicia)": "En Común-UP"}


def record_name(party: str) -> str:
    return RECORD_NAMES.get(party, re.sub(r"\s*\([^)]*list\)$", "", party))


def long_date(iso: str) -> str:
    return Fmt("en").date(iso)


def sig(x: float, digits: int = 2) -> str:
    return Fmt("en").sig(x, digits)


def pct(x: float, digits: int = 0) -> str:
    return Fmt("en").pct(x, digits)


ELECTIONS = {"2015": ("2015", "2015"), "2016": ("2016", "2016"),
             "2019A": ("April 2019", "abril de 2019"),
             "2019N": ("November 2019", "noviembre de 2019"), "2023": ("2023", "2023")}


# The variants of the robustness table (analysis.robustness), in both languages.
ROBUSTNESS_LABELS = {
    "base": ("Base: median of {firms} firms", "Base: mediana de {firms} empresas"),
    "weighted_mean": ("Mean weighted by sample size", "Media ponderada por la muestra"),
    "days7": ("Last 7 days only ({firms}\u00a0firms)",
              "Solo los últimos 7 días ({firms}\u00a0empresas)"),
    "house2023": ("Each firm corrected by its 2023 error",
                  "Cada empresa corregida por su error de 2023"),
    "no_cis": ("Without the CIS", "Sin el CIS"),
    "no_party_polls": ("Without the poll released by a party ({party})",
                       "Sin la encuesta publicada por un partido ({party})"),
    "normal_errors": ("Normal errors (no Student-t)", "Errores normales (sin la $t$)"),
    "student_t": ("Student-t errors", "Errores con la $t$ de Student"),
    "no_record_abstain": ("Lists with no 2023 seat abstain",
                          "Las listas sin escaño en 2023 se abstienen"),
}


# The same variant when more than one party has released a poll in the window.
PARTY_POLLS = ("Without the polls released by parties ({party})",
               "Sin las encuestas publicadas por partidos ({party})")


def robustness_label(fm: Fmt, row: dict, firms: str, party: str) -> str:
    en, es = ROBUSTNESS_LABELS[row["key"]]
    if row["key"] == "no_party_polls" and "," in party:
        en, es = PARTY_POLLS
    return fm.word(en, es).format(firms=row.get("firms", firms), party=party)


def compare(fm: Fmt, ratio: float, times: str | None, what: str) -> str:
    """How a probability compares with a reference, in words that stay true on a rerun."""
    if 2 / 3 < ratio < 3 / 2:
        return fm.word(f"close to the odds of {what}", f"parecida a la de {what}")
    if ratio >= 3 / 2:
        if times:
            return fm.word(f"about {times} times likelier than {what}",
                           f"unas {times} veces mayor que la de {what}")
        return fm.word(f"likelier than {what}", f"mayor que la de {what}")
    return fm.word(f"less likely than {what}", f"menor que la de {what}")


def small_pct(fm: Fmt, x: float) -> str:
    """One decimal; two below 0.1% so that a small number does not read as zero."""
    return fm.pct(x, 1 if x == 0 or x >= 0.001 else 2)


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
    f[f"{prefix}.blocked"] = small_pct(fm, g["blocked"])
    f[f"{prefix}.second"] = small_pct(fm, g["second_vote"])
    f[f"{prefix}.both"] = fm.pct(g["both_possible"], 2)


def _record_facts(f: dict[str, str], fm: Fmt, record: list[dict]) -> None:
    """Every vote of the investiture record (rec.1 … rec.N, in date order) and what the
    carousel and README say about it: which investitures passed only thanks to abstentions
    (rec.decided) and how many deputies abstained in the latest year (rec.last.abstain)."""
    if not record:
        return
    for i, v in enumerate(record, start=1):
        k = f"rec.{i}"
        f[f"{k}.date"] = fm.date(v["date"])
        for x in ("yes", "no", "abstain", "absent"):
            f[f"{k}.{x}"] = str(v[x])
        for x, word in (("yes", "yes_from"), ("abstain", "abstained")):
            f[f"{k}.{word}"] = ", ".join(f"{record_name(g['party'])} {g[x]}"
                                        for g in v["groups"] if g[x]) or "—"
    inv = [v for v in record if v["kind"] == "investiture"]
    f["rec.votes"] = str(len(inv))
    f["rec.debates"] = str(len({v["event"] for v in inv}))
    f["rec.first"] = record[0]["date"][:4]
    decided = [v for v in inv if v["passed"] and v["yes"] < 176 and v["abstain"]]
    f["rec.decided"] = fm.join([fm.month(v["date"]) for v in decided])
    f["rec.decided.n"] = str(len(decided))
    last = record[-1]["date"][:4]
    f["rec.last"] = last
    n = sum(v["abstain"] for v in record if v["date"][:4] == last)
    f["rec.last.abstain"] = str(n)
    f["rec.last.abstained"] = (fm.word("nobody abstained", "nadie se abstuvo") if n == 0 else
                               fm.word(f"{n} deputies abstained", f"se abstuvieron {n} diputados"))


def _sigma_facts(f: dict[str, str], fm: Fmt, meta: dict) -> None:
    """How the texts describe the national error, whichever way the pre-declared rule went
    (Student-t errors adopted or not): sigma.how, sigma.dist, sigma.alt, sigma.limit."""
    n = f["n_poll_errors"]
    if meta.get("student_t"):
        df = str(meta["sigma_df"])
        f["sigma.how"] = fm.word(
            f"Since σ is itself estimated from {n} errors, each simulated election draws its own "
            f"scale, σ·√(df/χ²), with df = {df} degrees of freedom: the errors are Student-t.",
            f"Como σ también se estima, con {n} errores, cada simulación saca su propia escala, "
            f"σ·√(gl/χ²), con {df} grados de libertad: los errores son t de Student.")
        f["sigma.dist"] = fm.word(f"Student-t, {df} degrees of freedom",
                                  f"t de Student, {df} grados de libertad")
        f["sigma.alt"] = fm.word("normal errors", "errores normales")
        f["sigma.limit"] = fm.word(
            f"The Student-t with {df} degrees of freedom still counts them as independent, so "
            "the tails may be somewhat heavier than modelled.",
            f"La t de Student con {df} grados de libertad aún los cuenta como independientes, "
            "así que las colas pueden ser algo más gruesas que en el modelo.")
        alt = "normal_errors"
    else:
        f["sigma.how"] = fm.word(
            f"σ is itself estimated from {n} errors; Student-t errors, which allow for that, are "
            "a variant.",
            f"σ también se estima, con {n} errores; los errores con la t de Student, que lo "
            "tienen en cuenta, son una variante.")
        f["sigma.dist"] = fm.word("normal", "normal")
        f["sigma.alt"] = fm.word("Student-t errors", "errores con la t de Student")
        f["sigma.limit"] = fm.word(
            "Normal errors take σ as known, so the tails may be somewhat heavier than modelled.",
            "Los errores normales dan σ por sabido, así que las colas pueden ser algo más gruesas "
            "que en el modelo.")
        alt = "student_t"
    f["sigma.alt.effect"] = f.get(f"rob.{alt}.effect", "—")


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
        gov = nat["government"]["one_in"]
        f["ratio_gse_gov"] = f"{s['context']['gse_2012_one_in'] / gov:.0f}"
        f["ratio_gov_seat"] = fm.sig(gov / nat["seat"]["one_in"])
        f["cmp.gov.lottery"] = compare(fm, LOTTERY / gov, None, fm.word(
            "picking all six numbers of 49", "acertar los seis números de la Primitiva"))
        f["cmp.gov.gse"] = compare(fm, s["context"]["gse_2012_one_in"] / gov,
                                   f["ratio_gse_gov"], fm.word(
                                       "deciding the 2008 US presidency",
                                       f"decidir las presidenciales de EE.{NBSP}UU. de 2008"))
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
    rob = s.get("robustness", [])
    party = ", ".join(polls["party_released"]) or fm.word("none", "ninguna")
    for r in rob:
        k = r["key"]
        f[f"rob.{k}.name"] = robustness_label(fm, r, str(polls["firms"]), party)
        if "n" in r:
            f["rob.n"] = fm.num(r["n"])
        if r.get("same_as_base"):
            f[f"rob.{k}.effect"] = fm.word("as the base", "como la base")
            continue
        f[f"rob.{k}.effect"] = small_pct(fm, r["PP"])
        for x in ("PP", "PSOE", "blocked"):
            f[f"rob.{k}.{x}"] = small_pct(fm, r[x])
        f[f"rob.{k}.second"] = small_pct(fm, r["second_vote"])
        f[f"rob.{k}.gov"] = fm.sig(r["government_one_in"])
        f[f"rob.{k}.seat"] = fm.sig(r["seat_one_in"])
        if "firms" in r:
            f[f"rob.{k}.firms"] = str(r["firms"])
    moved = [r for r in rob if r["key"] != "base" and not r.get("same_as_base")]
    if moved:
        base = next(r for r in rob if r["key"] == "base")
        big = max(moved, key=lambda r: abs(r["PP"] - base["PP"]))
        name = f[f"rob.{big['key']}.name"]
        f["rob.max.key"] = big["key"]
        f["rob.max.name"] = name[0].lower() + name[1:]
        for x in ("PP", "PSOE", "blocked", "gov"):
            f[f"rob.max.{x}"] = f[f"rob.{big['key']}.{x}"]
        f["rob.variants"] = str(len(moved))
        rows = [base, *moved]
        for x in ("PP", "PSOE"):
            lo, hi = min(r[x] for r in rows), max(r[x] for r in rows)
            f[f"rob.range.{x}"] = f"{small_pct(fm, lo)} {fm.word('to', 'a')} {small_pct(fm, hi)}"
        for r in moved:
            if "adjusted" in r:
                f[f"rob.{r['key']}.adjusted"] = fm.of(r["adjusted"], r["firms"])
        f["rob.max.assumes"] = fm.word(
            " It assumes each firm repeats its 2023 error.",
            " Supone que cada empresa repite su error de 2023.") \
            if big["key"] == "house2023" else ""
        cis_out = any(r["key"] == "no_cis" and r.get("same_as_base") for r in rob)
        f["rob.no_cis"] = (fm.word("No CIS poll falls in the window.",
                                   "No hay encuesta del CIS en el periodo.") if cis_out else "")
        f["cis.status"] = (fm.word(
            "The CIS falls outside the 14-day window; how it compares with the other firms is "
            "in the repository.",
            "El CIS cae fuera del periodo de 14 días; su comparación con las demás empresas "
            "está en el repositorio.") if cis_out else fm.word(
            f"The CIS is in the median; without it, the PP's candidate is invested in "
            f"{f.get('rob.no_cis.PP', '')} of the runs.",
            f"El CIS está en la mediana; sin él, el candidato del PP sale investido en el "
            f"{f.get('rob.no_cis.PP', '')} de las simulaciones."))
    comp = s.get("completeness")
    if comp:
        f["comp.candidacies"] = str(comp["candidacies"])
        f["comp.others"] = str(comp["in_others"])
        f["comp.with_past"] = str(len(comp["with_a_past_result"]))
        f["comp.flagged"] = str(len(comp["flagged"]))
        for i, r in enumerate(comp["with_a_past_result"][:10], start=1):
            f[f"comp.{i}.share"] = fm.pct(r["best_share"], 1)
            f[f"comp.{i}.min"] = fm.pct(r["min_winning_share"], 1)
        if comp["with_a_past_result"]:
            top = comp["with_a_past_result"][0]
            f["comp.top.list"] = top["list"]
            f["comp.top.where"] = top["constituency"]
            f["comp.top.share"] = fm.pct(top["best_share"], 1)
            f["comp.top.year"] = ELECTIONS[top["best_election"]][fm.es]
            f["comp.top.min"] = fm.pct(top["min_winning_share"], 1)
        f["comp.few_firms"] = ", ".join(comp["poll_columns_below_min_firms"]) or fm.word(
            "none", "ninguna")
        n_flag = len(comp["flagged"])
        f["comp.verdict"] = fm.word(
            "none has reached, in its constituency, the smallest share that has won a seat "
            "there since 2015",
            "ninguna ha llegado nunca en su circunscripción al porcentaje más bajo que ha dado "
            "un escaño allí desde 2015") if not n_flag else fm.word(
            f"{n_flag} have reached the smallest share that has won a seat there since 2015, "
            "so a seat for them is possible and not modelled",
            f"{n_flag} han llegado alguna vez al porcentaje más bajo que ha dado un escaño allí "
            "desde 2015: un escaño suyo es posible y no está en el modelo")
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
    f["bt.widen"] = (fm.word("no widening", "no se ensanchan") if bt["chosen_factor"] == 1 else
                     fm.word(f"every error widened by a factor of {f['bt.factor']}",
                             f"todos los errores se ensanchan por {f['bt.factor']}"))
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
    _record_facts(f, fm, ctx.get("record", []))
    sen = ctx.get("senate")
    if sen:
        for k, v in sen.items():
            if isinstance(v, int):
                f[f"senate.{k}"] = fm.num(v)
        f["senate.party_line_where"] = fm.join(sen["party_line_where"])
    f["n_backtest"] = fm.num(s["backtest"]["rule"]["n"])
    if meta.get("student_t"):
        f["sigma_df"] = str(meta["sigma_df"])
    _sigma_facts(f, fm, meta)
    f["bt.factors"] = ", ".join(fm.num(x, 2) for x in s["backtest"]["rule"]["factors"])
    m = re.fullmatch(r"(\d+) de (\w+) de (\d{4})", s["context"]["population"]["date"])
    if m:
        day = date(int(m[3]), MONTHS["es"].index(m[2]) + 1, int(m[1]))
        f["population_day"] = fm.date(day.isoformat())
    for k, v in th.get("canvass", {}).items():
        f[f"canvass.{k}"] = (fm.g(v) if isinstance(v, float) else fm.num(v)).replace("-", "−")
    sr = bt.get("sigma_rule")
    if sr:
        f["sr.lead"] = str(sr["lead_days"])
        f["sr.adopted"] = fm.word("Student-t", "t de Student") if sr["adopt_student_t"] else \
            fm.word("normal", "normal")
        for name, key in (("normal", "n"), ("student_t", "t")):
            for scope in ("all", "pair"):
                x = sr[name][scope]
                tag = f"sr.{key}" + ("" if scope == "all" else ".pair")
                f[f"{tag}.in80"] = fm.of(x["in80"], x["lists"])
                f[f"{tag}.in95"] = fm.of(x["in95"], x["lists"])
                f[f"{tag}.cov80"] = fm.pct(x["cov80"])
                f[f"{tag}.cov95"] = fm.pct(x["cov95"])
                f[f"{tag}.dist"] = fm.num(x["distance"], 3)
            for e, x in sr[name]["by_election"].items():
                f[f"sr.{key}.{e}.in80"] = fm.of(x["in80"], x["lists"])
                f[f"sr.{key}.{e}.in95"] = fm.of(x["in95"], x["lists"])
        t, n = sr["student_t"]["all"], sr["normal"]["all"]
        f["sr.result"] = fm.word(
            "so Student-t errors are adopted" if sr["adopt_student_t"] else
            "so the errors stay normal and the Student-t is a variant",
            "así que se adoptan los errores con la t de Student" if sr["adopt_student_t"] else
            "así que los errores siguen normales y la t de Student queda como variante")
        f["sr.closer"] = fm.word("closer to", "más cerca de") if t["distance"] < n["distance"] \
            else fm.word("no closer to", "no más cerca de")
        for run in sr["student_t" if sr["adopt_student_t"] else "normal"]["runs"]:
            e = run["election"]
            f[f"sr.{e}.cutoff"] = fm.date(run["cutoff"])
            f[f"sr.{e}.firms"] = str(run["firms"])
            f[f"sr.{e}.sigma"] = fm.num(run["calibration"]["sigma_national_logit"], 2)
            f[f"sr.{e}.n_errors"] = str(run["calibration"]["n_poll_errors"])
            f[f"sr.{e}.name"] = ELECTIONS[e][fm.es]
            misses = [x for x in run["lists"] if x["counted"] and not x["in80"]]
            f[f"sr.{e}.misses80"] = ", ".join(
                f"{DISPLAY.get(x['list'], x['list'])} ({x['actual']} {vs} {x['lo80']}–"
                f"{x['hi80']})" for x in misses) or fm.word("none", "ninguna")
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
    return re.sub(r"\b(?:arts?\.|articles?|artículos?)\s*\d+(?:\.\d+)?"
                  r"(?:\s*(?:[–-]|and|to|y|a)\s*\d+(?:\.\d+)?)*", " ", text, flags=re.I)


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
