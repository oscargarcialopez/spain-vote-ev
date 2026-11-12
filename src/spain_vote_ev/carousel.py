"""The LinkedIn carousel: 4:5 pages (6 x 7.5 in, previews at 1080 x 1350 px) set like a paper,
in Spanish (carousel/, the one published) or English (carousel/en/). STIX Two type (vendored in
fonts/), numbered sections and equations, captioned figures, ruled tables and the references;
black and greys and one brown accent that is no party's colour. Typst sets the pages and
matplotlib draws the figures as SVG (English PNG copies go to figures/ for the README).

Type is read on a phone: every size comes from legibility.py, whose floor is the smallest
type read at full speed on the narrowest common phone. Body text sits exactly on the floor and
nothing is smaller; figures are drawn at the text width and embedded at 100%, so their points
are the page's points. One idea per page.

Every number comes from results/summary.json through facts.build(), formatted for the page's
language. slides.txt holds the pages as plain text: a text alternative, and the input for
`voteev check`.
"""

from __future__ import annotations

import logging
import re
from pathlib import Path

import numpy as np
import typst
from matplotlib.font_manager import FontProperties
from matplotlib.patches import Rectangle
from matplotlib.textpath import TextPath

from . import facts as fx
from . import legibility as lg
from . import style, theory
from .parties import DISPLAY
from .style import ACCENT, FILL, GREY, INK, plt

AUTHOR = "Óscar García López"
REPO = "github.com/oscargarcialopez/spain-vote-ev"
MARGIN_X = 0.45  # inches
TEXT_W = lg.PAGE_W_IN - 2 * MARGIN_X  # 5.1 in: figures are drawn at this width
NB = fx.NBSP
USA = f"EE.{NB}UU."
PT = lg.BODY_PT  # every text in the figures

META = {
    "en": {"title": "What is one vote worth?",
           "subtitle": "Spain's general election of 29 November 2026",
           "date": "November 2026", "abstract": "Abstract", "figure": "Figure",
           "table": "Table", "slide": "Slide", "references": "References",
           "typst": 'lang: "en", region: "gb"'},
    "es": {"title": "¿Cuánto vale un voto?",
           "subtitle": "Elecciones generales del 29 de noviembre de 2026",
           "date": "noviembre de 2026", "abstract": "Resumen", "figure": "Figura",
           "table": "Tabla", "slide": "Diapositiva", "references": "Referencias",
           "typst": 'lang: "es", region: "ES"'},
}

# Author (year). Title. Journal (or publisher, for a book, whose title is in italics).
# Kept in English, with their original titles, in both carousels.
REFERENCES = [
    ("Banzhaf", "1965", "Weighted voting doesn't work.", "Rutgers Law Review", False),
    ("Downs", "1957", "An Economic Theory of Democracy.", "Harper", True),
    ("Edlin, Gelman & Kaplan", "2007", "Voting as a rational choice.",
     "Rationality and Society", False),
    ("Gelman, Silver & Edlin", "2012", "What is the probability your vote will make a "
     "difference?", "Economic Inquiry", False),
    ("Gerber, Green & Larimer", "2008", "Social pressure and voter turnout.",
     "American Political Science Review", False),
    ("Kalla & Broockman", "2018", "The minimal persuasive effects of campaign contact in "
     "general elections.", "American Political Science Review", False),
    ("Riker & Ordeshook", "1968", "A theory of the calculus of voting.",
     "American Political Science Review", False),
    ("Shapley & Shubik", "1954", "A method for evaluating the distribution of power in a "
     "committee system.", "American Political Science Review", False),
    ("Strøm", "1990", "A behavioral theory of competitive political parties.",
     "American Journal of Political Science", False),
]

PREAMBLE = r"""
#set document(title: "@TITLE", author: "@AUTHOR", date: none)
#set page(
  width: @PAGE_Win, height: @PAGE_Hin,
  margin: (x: @MARGIN_Xin, top: 0.8in, bottom: 0.62in),
  header-ascent: 28%,
  header: context if here().page() > 1 {
    set text(@ITALICpt, style: "italic")
    align(center, [@HEADER])
    v(-5pt)
    line(length: 100%, stroke: 0.4pt)
  },
  footer: context align(center, text(@BODYpt)[#here().page()]),
)
#set text(font: ("STIX Two Text", "STIX Two Math"), size: @BODYpt, @LANG)
#show emph: set text(size: @ITALICpt)
#show regex("@NAMES"): set text(hyphenate: false)
#show math.equation: set text(font: "STIX Two Math")
#set par(justify: true, leading: 0.5em, spacing: 0.85em)
#set heading(numbering: "1.")
#show heading: set text(@HEADINGpt, weight: "bold")
#show heading: set block(above: 0pt, below: 0.8em)
#show heading.where(level: 2): set text(@BODYpt)
#show heading.where(level: 2): set block(above: 1.1em, below: 0.7em)
#set math.equation(numbering: "(1)")
#set list(indent: 0em, body-indent: 0.5em, spacing: 0.75em, marker: [•])
#show list: set par(justify: false)
#let cap(kind, n, body, above: 0.6em) = block(above: above, below: 1em, {
  set par(justify: false)
  [#strong[#kind #n.] #body]
})
#let ruled(cols, aligns, header, gutter: 0pt, ..rows) = align(center, {
  set par(justify: false, leading: 0.4em)
  table(
    columns: cols, align: aligns, stroke: none, inset: (x: 4pt, y: 3.6pt), row-gutter: gutter,
    table.hline(stroke: 0.9pt),
    table.header(..header),
    table.hline(stroke: 0.5pt),
    ..rows,
    table.hline(stroke: 0.9pt),
  )
})
"""

# Spanish day and month, millions, percentages and euros stay on one line:
# 10 de noviembre, 10,8 millones, 3 %, 5 €.
UNBROKEN_ES = re.compile(r"\d+ de (?:" + "|".join(fx.MONTHS["es"]) + r")\b"
                         r"|\d (?:millones|millón)\b|\d [%€]")
# "1 in 76,000", "1 entre 10,8 millones" stay on one line, in both languages.
ONE_IN = re.compile(r"\b1 (?:in|entre) [\d.,]+(?: (?:million|billion|millones|millón)\b)?")
# "22 of 26", "22 de 26": a count stays on one line.
OF = re.compile(r"(?<![\d.,])\d+ (?:of|de) \d+\b")
# "$x$ = value": no line break on either side of the sign.
EQUALS = re.compile(r"(?<!\\)\$ = ")
# Authors' names are not hyphenated.
NAMES = sorted({n for authors, *_ in REFERENCES for n in re.split(r", | & ", authors)})


class Lang:
    """A page's language: L(english, spanish) picks one, with its no-break spaces."""

    def __init__(self, code: str):
        if code not in META:
            raise ValueError(f"unknown language {code!r}")
        self.code, self.es, self.meta = code, code == "es", META[code]

    def __call__(self, en, es):
        text = es if self.es else en
        if not isinstance(text, str):
            return text
        text = ONE_IN.sub(lambda m: m.group().replace(" ", NB), text)
        text = EQUALS.sub(f"${NB}={NB}", text)
        text = OF.sub(lambda m: m.group().replace(" ", NB), text)
        if self.es:
            text = UNBROKEN_ES.sub(lambda m: m.group().replace(" ", NB), text)
        return text


def mnum(x: str) -> str:
    """A number inside $math$: a decimal comma is text there, not a separator."""
    return f'"{x}"' if "," in x else x


MATH_DOLLAR = re.compile(r"(?<!\\)\$")


def _esc(text: str) -> str:
    """Plain text as Typst markup: escape what would start markup; a literal $ is \\$."""
    text = text.replace("\\$", "\x00")
    text = re.sub(r"([\\#*_@<>\[\]`~/=+-])", r"\\\1", text)
    return text.replace("\x00", "\\$")


UNBREAKABLE = re.compile(f"[^ \t\n{NB}]+(?:{NB}[^ \t\n{NB}]+)+")


def _keep(markup: str) -> str:
    """Words joined by no-break spaces are not hyphenated either."""
    return UNBREAKABLE.sub(lambda m: f"#text(hyphenate: false)[{m.group()}]", markup)


def T(src: str) -> str:
    """Typst markup from text with $inline math$ (Typst math syntax)."""
    parts = MATH_DOLLAR.split(src)
    return "".join(_keep(_esc(p)) if i % 2 == 0 else f"#box[${p}$]"
                   for i, p in enumerate(parts))


GREEK = {"Delta": "Δ", "alpha": "α", "sigma": "σ", "approx": "≈", "<=": "≤", ">=": "≥",
         "dot": "·", "times": "×", "\\/": "/"}


def P(src: str) -> str:
    """The same text, plain: math loses its Typst syntax."""
    parts = MATH_DOLLAR.split(src)
    out = []
    for i, p in enumerate(parts):
        if i % 2 == 0:
            out.append(p.replace("\\$", "$"))
            continue
        for k, v in GREEK.items():
            p = p.replace(k, v)
        out.append(p.replace('"', "").replace("  ", " "))
    return "".join(out)


def nb(text: str) -> str:
    """No line breaks inside: day and month stay together."""
    return text.replace(" ", NB).replace(f"{NB}–{NB}", " – ")


def cell(x: str) -> str:
    """A table cell; a newline in the text is a line break."""
    return "[" + " \\ ".join(T(part) for part in x.split("\n")) + "]"


class Page:
    """One page: Typst markup blocks and the same content as plain text, in reading order."""

    def __init__(self, L: Lang):
        self.L = L
        self.typ: list[str] = []
        self.txt: list[str] = []
        self.refs: list[str] = []

    def raw(self, typ: str, txt: str | list[str] = ()) -> None:
        self.typ.append(typ)
        self.txt += [txt] if isinstance(txt, str) else list(txt)

    def h(self, src: str) -> None:
        self.raw(f"= {T(src)}", P(src))

    def p(self, src: str) -> None:
        self.raw(T(src), P(src))

    def run_in(self, word: str, src: str) -> None:
        """A paragraph led by a word in bold: Resumen. Límites. Conclusiones."""
        self.raw(f"#strong[{T(word)}] " + T(src), f"{word} {P(src)}")

    def eq(self, math: str, n: int) -> None:
        """A numbered display equation; no subscripts or superscripts (they shrink)."""
        if re.search(r"[_^]|\bfrac\b", math):
            raise ValueError(f"equation with a script or a fraction: {math}")
        self.raw(f"$ {math} $", f"{P('$' + math + '$')} ({n})")

    def bullets(self, srcs: list[str]) -> None:
        self.raw("\n".join(f"- {T(s)}" for s in srcs), [P(s) for s in srcs])

    def figure(self, name: str, n: int, caption: str, labels: list[str]) -> None:
        kind = self.L.meta["figure"]
        self.raw(f'#align(center, image("{name}", width: {TEXT_W}in))\n'
                 f'#cap("{kind}", {n})[{T(caption)}]',
                 [f"{kind} {n}. {P(caption)}"] + labels)

    def table(self, cols: str, aligns: str, header: list[str], rows: list[list[str]],
              caption: str | None = None, n: int | None = None, gutter: str = "0pt") -> None:
        cells = ", ".join(cell(x) for r in rows for x in r)
        typ = (f"#ruled({cols}, {aligns}, ({', '.join(cell(h) for h in header)},), {cells}, "
               f"gutter: {gutter})")
        txt = [" | ".join(h.replace("\n", " ") for h in header)]
        txt += [" | ".join(P(x).replace("\n", " ") for x in r) for r in rows]
        if caption:
            kind = self.L.meta["table"]
            typ = f'#cap("{kind}", {n}, above: 0.9em)[{T(caption)}]\n' + typ
            txt = [f"{kind} {n}. {P(caption)}"] + txt
        self.raw(typ, txt)

    def markup(self) -> str:
        return "\n\n".join(self.typ)


# --- figures --------------------------------------------------------------------------------
# Drawn at TEXT_W and embedded at 100%: a figure's points are the page's points, so every
# text is set at the floor size (PT). Few ticks, direct labels, short axis titles.


def texts(fig) -> list[str]:
    """The words on a figure that are not tick numbers."""
    out = []
    for ax in fig.axes:
        out += [t.get_text() for t in ax.texts]
        out += [ax.get_title(), ax.get_xlabel(), ax.get_ylabel()]
        for t in [*ax.get_yticklabels(), *ax.get_xticklabels()]:
            if re.search("[A-Za-z]", t.get_text()):
                out.append(t.get_text())
        if ax.get_legend():
            out += [t.get_text() for t in ax.get_legend().get_texts()]
    out += [t.get_text() for t in fig.texts]
    if fig._supxlabel is not None:
        out.append(fig._supxlabel.get_text())
    return [t.replace("\n", " ") for t in out if t.strip()]


def save(fig, name: str, svg: Path, png: Path | None) -> list[str]:
    """Check the figure against the type floor, then write it at exactly TEXT_W wide."""
    bad = lg.figure_violations(fig, name)
    if bad:
        raise ValueError("figure below the type floor:\n  " + "\n  ".join(bad))
    labels = texts(fig)
    fig.savefig(svg, format="svg", metadata={"Date": None})
    width = float(re.search(r'<svg[^>]*\swidth="([\d.]+)pt"', svg.read_text())[1])
    if abs(width - TEXT_W * 72) > 0.01:
        raise ValueError(f"{svg.name} is {width} pt wide, not {TEXT_W * 72} pt")
    if png is not None:
        fig.savefig(png, format="png", dpi=200, metadata={"Software": None})
    plt.close(fig)
    return labels


def figure(height_in: float):
    """A figure the width of the text, laid out so that nothing falls off the canvas."""
    return plt.figure(figsize=(TEXT_W, height_in), layout="constrained")


def fig_odds(s: dict, f: dict, L: Lang):
    """Four bars on a log scale, each with its label above and its odds at the right."""
    nat = s["vote"]["national"]
    rows = [(L("One vote changes a seat", "Un voto cambia un escaño"),
             nat["seat"]["one_in"], f["seat.one_in"], True),
            (L("One vote decides whether a bloc has 176",
               "Un voto decide si un bloque llega a 176"),
             nat["majority_any"]["one_in"], f["majority_any.one_in"], True),
            (L("Picking all six numbers of 49", "Acertar los seis números de la Primitiva"),
             fx.LOTTERY, f["lottery"], False),
            (L("One vote decides the 2008 US presidency",
               f"Un voto decide las presidenciales de {USA} de 2008"),
             s["context"]["gse_2012_one_in"], f["gse"], False)]
    pitch, bar, top = 40.0, 11.0, 4.0  # pt
    w, h = TEXT_W * 72, len(rows) * pitch + top
    fig = plt.figure(figsize=(TEXT_W, h / 72))
    ax = fig.add_axes((0, 0, 1, 1))
    ax.set_xlim(0, w)
    ax.set_ylim(0, h)
    ax.axis("off")
    span = 0.6 * w / np.log10(max(v for _, v, _, _ in rows))  # pt per decade
    for k, (label, val, txt, ours) in enumerate(rows):
        y = h - top - k * pitch
        ax.text(0, y, label, fontsize=PT, va="top")
        y_bar = y - 19 - bar
        ax.add_patch(Rectangle((0, y_bar), np.log10(val) * span, bar, lw=0.7, ec=INK,
                               fc=INK if ours else "white", hatch=None if ours else "////"))
        ax.text(w, y_bar + bar / 2, f"{L('1 in', '1 entre')} {txt}", fontsize=PT, ha="right",
                va="center_baseline")
    return fig


ELECTION_NAME = {"en": {"2019N": "November 2019", "2023": "July 2023"},
                 "es": {"2019N": "Noviembre de 2019", "2023": "Julio de 2023"}}


def text_width(text: str) -> float:
    """Width in pt of a text at the floor size."""
    prop = FontProperties(family="STIX Two Text", size=PT)
    return TextPath((0, 0), text, prop=prop).get_extents().width


def fig_backtests(s: dict, f: dict, L: Lang):
    """One panel per election, side by side. At the floor size a column of list names would
    leave each panel too narrow, so every list is named next to its own interval: on the
    right if it fits, otherwise on the left (the first panel keeps a margin for that)."""
    runs = s["backtest"]["runs"]
    w, h = TEXT_W * 72, 4.95 * 72  # pt
    left, gap, bottom, top_pad, pad = 74.0, 14.0, 44.0, 24.0, 5.0
    widths = [(w - left - gap) * 0.51, (w - left - gap) * 0.49]
    starts = [left, left + widths[0] + gap]
    fig = plt.figure(figsize=(w / 72, h / 72))
    vmax = max(x["hi95"] for run in runs for x in run["lists"]) * 1.05
    for run, x0, width in zip(runs, starts, widths, strict=True):
        ax = fig.add_axes((x0 / w, bottom / h, width / w, (h - bottom - top_pad) / h))
        scale = width / np.sqrt(vmax)  # pt per square-root unit
        rows = sorted((x for x in run["lists"] if x["counted"]), key=lambda x: x["actual"])
        for y, x in enumerate(rows):
            ax.plot([x["lo95"], x["hi95"]], [y, y], color=INK, lw=1.0, solid_capstyle="butt",
                    clip_on=False)
            ax.plot([x["lo80"], x["hi80"]], [y, y], color=INK, lw=3.6,
                    solid_capstyle="projecting", clip_on=False)
            ax.plot([x["actual"]], [y], "D", ms=6, mec=ACCENT, mew=1.2,
                    mfc="white" if x["in80"] else ACCENT, clip_on=False, zorder=4)
            name = DISPLAY.get(x["list"], x["list"])
            hi = max(x["hi95"], x["actual"])
            if np.sqrt(hi) * scale + pad + 4 + text_width(name) <= width:
                at, dx, ha = hi, pad + 4, "left"
            else:
                at, dx, ha = min(x["lo95"], x["actual"]), -pad - 4, "right"
            ax.annotate(name, (at, y), xytext=(dx, 0), textcoords="offset points", ha=ha,
                        va="center_baseline", fontsize=PT)
        ax.set_xscale("function", functions=(lambda v: np.sqrt(np.clip(v, 0, None)), np.square))
        ax.set_xlim(0, vmax)
        ax.set_xticks([0, 10, 100], ["0", "10", "100"])
        ax.minorticks_off()
        ax.set_yticks([])
        ax.tick_params(axis="x", top=False)
        for side in ("top", "left", "right"):
            ax.spines[side].set_visible(False)
        ax.set_ylim(-0.7, len(rows) - 0.3)
        ax.set_title(ELECTION_NAME[L.code][run["election"]], fontsize=PT, pad=5)
    fig.text((left + w) / 2 / w, 3 / h, L("seats (square-root scale)",
                                          "escaños (escala de raíz cuadrada)"),
             ha="center", va="bottom", fontsize=PT)
    return fig


def fig_seats(s: dict, f: dict, L: Lang):
    lists = [(k, v) for k, v in s["lists"].items() if v["mean"] >= 0.5]
    lists.sort(key=lambda kv: kv[1]["mean"])
    fig = figure(3.3)
    ax = fig.subplots()
    for y, (_, v) in enumerate(lists):
        ax.plot([v["lo95"], v["hi95"]], [y, y], color=INK, lw=1.0, solid_capstyle="butt")
        ax.plot([v["lo80"], v["hi80"]], [y, y], color=INK, lw=3.6, solid_capstyle="butt")
        ax.plot([v["mean"]], [y], "o", ms=6, mfc="white", mec=INK, mew=1.1)
    ax.set_yticks(range(len(lists)), [v["name"] for _, v in lists])
    ax.set_xlim(0, 180)
    ax.set_xticks([0, 50, 100, 150])
    ax.set_ylim(-0.6, len(lists) - 0.4)
    ax.tick_params(axis="y", length=0)
    return fig


ODDS_TICKS_Y = {"en": ["10,000", "1 million", "100 million"],
                "es": ["10.000", "1 millón", "100 millones"]}
# Where the names of the extreme constituencies go: offset in points and alignment.
LABEL_AT = {"seat.top1": (7, -5, "left"), "seat.bottom1": (-7, 8, "right"),
            "majority_any.bottom1": (-7, 0, "right"), "majority_any.top2": (10, -14, "left")}


def fig_constituencies(s: dict, f: dict, L: Lang):
    prov = s["vote"]["provinces"]
    seats = np.array([r["seats"] for r in prov], float)
    jitter = 1 + 0.035 * (np.arange(len(prov)) % 3 - 1)
    fig = figure(3.2)
    ax = fig.subplots()
    ax.plot(seats * jitter, [r["one_in_seat"] for r in prov], "o", ms=5, mfc=INK, mec=INK,
            mew=0.5)
    ax.plot(seats * jitter, [r["one_in_majority_any"] for r in prov], "o", ms=5.2,
            mfc="white", mec=ACCENT, mew=1.1)
    ax.set_xscale("log")
    ax.set_yscale("log")
    top = int(seats.max())
    ax.set_xlim(0.8, top * 1.35)
    ax.set_ylim(2e3, 6e8)
    ax.set_xticks([1, 3, 10, top], ["1", "3", "10", str(top)])
    ax.minorticks_off()
    ax.set_yticks([1e4, 1e6, 1e8], ODDS_TICKS_Y[L.code])
    ax.set_xlabel(L("seats in the constituency", "escaños de la circunscripción"))
    ax.set_ylabel(L("1 in N", "1 entre N"))
    ax.text(1.0, 2.6e8, L("the majority", "la mayoría"), fontsize=PT, color=ACCENT, va="center")
    ax.text(9, 4.5e3, L("a seat", "un escaño"), fontsize=PT, va="center")
    for key, (dx, dy, ha) in LABEL_AT.items():
        r = next(x for x in prov if x["name"] == f[key])
        ev = "seat" if key.startswith("seat") else "majority_any"
        arrow = {"arrowstyle": "-", "lw": 0.6, "color": GREY} if abs(dy) > 10 else None
        ax.annotate(r["name"], (r["seats"], r[f"one_in_{ev}"]), xytext=(dx, dy), ha=ha,
                    va="center", textcoords="offset points", fontsize=PT, color=GREY,
                    arrowprops=arrow)
    return fig


def fig_break_even(s: dict, f: dict, L: Lang):
    th = s["theory"]
    b = theory.B_GRID
    fig = figure(3.0)
    ax = fig.subplots()
    a_maj = theory.break_even_alpha(th["majority"]["p"], th["population"], b)
    a_seat = theory.break_even_alpha(th["seat"]["p"], th["population"], b)
    ax.fill_between(b, a_maj, 1, color=FILL, lw=0)
    ax.plot(b, a_maj, color=INK, lw=1.4)
    ax.plot(b, a_seat, color=GREY, lw=1.3, ls="--")
    ax.plot([100], [th["majority"]["alpha_for_b_100"]], "o", ms=6, mfc="white", mec=ACCENT,
            mew=1.3)
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlim(1, 1e5)
    ax.set_ylim(1e-6, 1)
    ax.set_xticks([1, 100, 1e4], ["1", "100", L("10,000", "10.000")])
    ax.set_yticks([1e-4, 1e-2, 1], L(["0.01%", "1%", "100%"],
                                     [f"0,01{NB}%", f"1{NB}%", f"100{NB}%"]))
    ax.minorticks_off()
    ax.text(30, 0.12, L("voting pays", "votar compensa"), fontsize=PT, va="center")
    ax.text(300, 1e-4, L("majority", "mayoría"), fontsize=PT, va="center")
    ax.text(40, 5e-6, L("a seat", "un escaño"), fontsize=PT, va="center", color=GREY)
    ax.set_xlabel(L("gain per person from the outcome, b (€)",
                    "lo que gana cada persona, b (€)"))
    ax.set_ylabel(L("weight on others, α", "peso de los demás, α"))
    return fig


FIGURES = {"fig-odds": fig_odds, "fig-backtests": fig_backtests, "fig-seats": fig_seats,
           "fig-constituencies": fig_constituencies, "fig-break-even": fig_break_even}


def draw(name: str, s: dict, f: dict, L: Lang, out: Path, png: Path | None) -> list[str]:
    """Draw a figure, check it, save it as out/name.svg (and png/name.png)."""
    fig = FIGURES[name](s, f, L)
    return save(fig, name, out / f"{name}.svg", png and png / f"{name}.png")


def figure_violations(summary: dict, lang: str) -> list[str]:
    """Every text in every figure of one language's carousel against the type floor."""
    style.paper_style()
    L, f = Lang(lang), fx.build(summary, lang)
    out = []
    for name, make in FIGURES.items():
        fig = make(summary, f, L)
        out += lg.figure_violations(fig, f"{lang}/{name}")
        if abs(fig.get_figwidth() - TEXT_W) > 1e-9:
            out.append(f"{lang}/{name}: {fig.get_figwidth()} in wide, not {TEXT_W} in")
        plt.close(fig)
    return out


# --- the pages ------------------------------------------------------------------------------


def compare(L: Lang, ratio: float, times: str | None, what: str) -> str:
    """How a probability compares with a reference, in words that stay true on a rerun."""
    if 2 / 3 < ratio < 3 / 2:
        return L(f"close to the odds of {what}", f"parecida a la de {what}")
    if ratio >= 3 / 2:
        if times:
            return L(f"about {times} times likelier than {what}",
                     f"unas {times} veces mayor que la de {what}")
        return L(f"likelier than {what}", f"mayor que la de {what}")
    return L(f"less likely than {what}", f"menor que la de {what}")


def race(L: Lang, seats: str) -> str:
    if seats == "1":
        return L("a one-seat race", "que elige un solo diputado")
    return L(f"with {seats} seats", f"que elige {seats} diputados")


def page_title(s: dict, f: dict, L: Lang, out: Path, png: Path | None) -> Page:
    pg, m = Page(L), L.meta
    byline = f"{AUTHOR} · {m['date']}"
    pg.raw("#v(-0.35in)\n#align(center)[\n"
           f"  #text({lg.TITLE_PT}pt, weight: \"bold\", hyphenate: false)[{T(m['title'])}]\n"
           f"  #v(-1pt)\n  #text({lg.ITALIC_PT}pt, style: \"italic\")[{T(m['subtitle'])}]\n"
           f"  #v(-1pt)\n  {T(byline)}\n]\n#v(4pt)",
           [m["title"], m["subtitle"], byline])
    abstract = L(
        f"I simulate Spain's election {f['n']} times from the polls to {nb(f['cutoff'])}. For "
        f"the average voter, one more vote changes a seat with probability 1 in "
        f"{f['seat.one_in']}, and decides whether either 2023 investiture bloc reaches 176 "
        f"seats with probability 1 in {f['majority_any.one_in']}. Every list follows the same "
        "rules, and nothing here advises anyone.",
        f"Simulo {f['n']} veces las generales con las encuestas hasta el {f['cutoff']}. Para "
        "el votante medio, un voto más cambia un escaño con una probabilidad de 1 entre "
        f"{f['seat.one_in']}, y decide si uno de los bloques de las investiduras de 2023 llega "
        f"a 176 escaños con una de 1 entre {f['majority_any.one_in']}. Todas las listas siguen "
        "las mismas reglas, y no aconsejo nada a nadie.")
    pg.run_in(m["abstract"] + ".", abstract)
    labels = draw("fig-odds", s, f, L, out, png)
    pg.figure("fig-odds.svg", 1, L(
        "Log scale. Hatched: references (2008: Gelman, Silver and Edlin, 2012).",
        "Escala logarítmica. Rayado: referencias (la de 2008, de Gelman, Silver y Edlin, "
        "2012)."), labels)
    note = L("Code and data: link in the first comment.",
             "Código y datos: enlace en el primer comentario.")
    pg.raw(f"#v(1fr)\n#align(center)[{T(note)}]", P(note))
    return pg


def yes(f: dict, who: str, parties: list[tuple[str, str]]) -> str:
    """'PP 137, Vox 33, …', each name with its number on one line."""
    return ", ".join(f"{name.replace(' ', NB)}{NB}{f[f'{who}.{code}']}" for name, code in parties)


def page_question(s: dict, f: dict, L: Lang, out: Path, png: Path | None) -> Page:
    pg = Page(L)
    pg.h(L("The question", "La pregunta"))
    pg.p(L("Spain elects 350 deputies in 52 constituencies by D'Hondt, with a 3% threshold in "
           "each. One more vote can move a seat from one list to another, or move the seat "
           "that decides the absolute majority: 176.",
           "España elige 350 diputados en 52 circunscripciones por D'Hondt, con un umbral del "
           "3 % en cada una. Un voto más puede pasar un escaño de una lista a otra, o mover el "
           "escaño que decide la mayoría absoluta: 176."))
    pg.p(L("For the majority I use the coalitions of the two 2023 investiture votes, so no "
           "party is placed by anyone's judgement:",
           "Para la mayoría uso los bloques de las dos investiduras de 2023; así nadie coloca "
           "a ningún partido a mano:"))
    fe, sa = "inv.feijoo", "inv.sanchez"
    pg.table("(auto, 1fr)", "(center, left)",
             [L("Bloc", "Bloque"), L("Yes votes", "Votos a favor")], [
        ["F", L(f"Feijóo, 27 September 2023: {f[fe + '.yes']}",
                f"Feijóo, 27 de septiembre de 2023: {f[fe + '.yes']}") + "\n"
         + yes(f, fe, [("PP", "PP"), ("Vox", "VOX"), ("UPN", "UPN"), ("CC", "CC")])],
        ["S", L(f"Sánchez, 16 November 2023: {f[sa + '.yes']}",
                f"Sánchez, 16 de noviembre de 2023: {f[sa + '.yes']}") + "\n"
         + yes(f, sa, [("PSOE", "PSOE"), ("Sumar", "SUMAR"), ("ERC", "ERC"),
                       ("Junts", "JUNTS"), ("EH Bildu", "BILDU"), ("PNV", "PNV"),
                       ("BNG", "BNG"), ("CC", "CC")])]], gutter="6pt")
    pg.p(L("Frente Amplio and Podemos, both in Sumar's group in 2023, count in S; lists with "
           "no seat in 2023 count in neither; Coalición Canaria voted yes twice, so it is in "
           "both. I also report S without Junts.",
           "Frente Amplio y Podemos, del grupo de Sumar en 2023, cuentan en S; las listas sin "
           "escaño en 2023, en ninguno; Coalición Canaria votó sí las dos veces y está en los "
           "dos. También doy S sin Junts."))
    return pg


def page_model(s: dict, f: dict, L: Lang, out: Path, png: Path | None) -> Page:
    pg = Page(L)
    pg.h(L("The model", "El modelo"))
    pg.bullets([
        L(f"Polls: each firm's latest poll with fieldwork ending {nb(f['window'])}; "
          f"{f['firms']} firms, none excluded. I take the median of each list.",
          "Encuestas: de cada empresa, la última con el trabajo de campo acabado "
          f"{f['window_between']}; {f['firms']} empresas, ninguna excluida. Tomo la mediana "
          "de cada lista."),
        L(f"National error: each share moves on the logit scale with "
          f"$sigma = {f['sigma_nat']}$, the size of the same median's errors {f['lead']} days "
          f"out in 2015–2023 ({f['n_poll_errors']} cases), centred on zero.",
          "Error nacional: cada lista se mueve en escala logit con "
          f"$sigma = {mnum(f['sigma_nat'])}$, lo que falló esa misma mediana a {f['lead']} "
          f"días en 2015–2023 ({f['n_poll_errors']} casos), centrado en cero."),
        L("Constituencies: proportional swing from 2023, with regional and provincial "
          f"deviations ($sigma = {f['tau_ccaa']}$ and {f['tau_prov']}) estimated from past "
          "swings; turnout varies too. SALF and the split of Sumar's vote start from the "
          "2024 European vote.",
          "Circunscripciones: cambio proporcional desde 2023, con desviaciones autonómicas y "
          f"provinciales ($sigma = {mnum(f['tau_ccaa'])}$ y {f['tau_prov']}) medidas en "
          "cambios pasados; la participación también varía. SALF y el reparto del voto de "
          "Sumar parten de las europeas de 2024."),
        L("Seats: D'Hondt with the 3% threshold; for each list, $Delta$ is the extra votes it "
          "needs for one more seat.",
          "Escaños: D'Hondt con el umbral del 3 %; para cada lista, $Delta$ son los votos que "
          "le faltan para un escaño más.")])
    if f["party_released"] not in ("none", "ninguna"):
        pg.p(L(f"One poll in the window was released by a party ({f['party_released']}); "
               f"without it, $P(F >= 176)$ is {f['sens.F.p']} instead of {f['bloc.F.p1']} and "
               f"$P(S >= 176)$ {f['sens.S.p']} instead of {f['bloc.S.p1']}.",
               f"Una encuesta la publicó un partido ({f['party_released']}); sin ella, "
               f"$P(F >= 176)$ es {f['sens.F.p']} en vez de {f['bloc.F.p1']}, y "
               f"$P(S >= 176)$, {f['sens.S.p']} en vez de {f['bloc.S.p1']}."))
    return pg


def page_decisive(s: dict, f: dict, L: Lang, out: Path, png: Path | None) -> Page:
    pg = Page(L)
    pg.h(L("The chance of deciding", "La probabilidad de decidir"))
    pg.p(L("One vote decides a seat when a list is one vote short of it. That chance is the "
           "density of $Delta$ at zero:",
           "Un voto decide un escaño cuando a una lista le falta un solo voto para ganarlo. "
           "Esa probabilidad es la densidad de $Delta$ en cero:"))
    pg.eq("p approx k \\/ (n dot h)", 1)
    pg.p(L(f"where $k$ counts the runs, out of $n$ = {f['n']}, with $0 < Delta <= h$, and $h$ "
           "is 2% of the constituency's votes per seat. With $h$ from 1% to 5%, the national "
           f"answers move by {f['seat.bw_spread']} (seat) and {f['majority_any.bw_spread']} "
           "(majority).",
           f"donde $k$ cuenta las simulaciones, de $n$ = {f['n']}, con $0 < Delta <= h$, y $h$ "
           "es el 2 % de los votos por escaño de la circunscripción. Con $h$ entre el 1 % y el "
           f"5 %, los resultados nacionales se mueven un {f['seat.bw_spread']} (escaño) y un "
           f"{f['majority_any.bw_spread']} (mayoría)."))
    pg.p(L("For the majority, only the runs where that seat moves a bloc across 176 count.",
           "Para la mayoría solo cuentan las simulaciones en que ese escaño cambia si un "
           "bloque llega a 176."))
    pg.p(L("The average voter weights each constituency and list by its expected votes: it is "
           "the chance for a vote picked at random.",
           "El votante medio pondera cada circunscripción y cada lista por sus votos "
           "esperados: es la probabilidad para un voto tomado al azar."))
    return pg


def page_backtest(s: dict, f: dict, L: Lang, out: Path, png: Path | None) -> Page:
    pg = Page(L)
    pg.h(L("Does it work? Backtests", "¿Funciona? Contraste con el pasado"))
    pg.p(L("I ran the same code seven days before the elections of November 2019 and July "
           "2023, calibrated only on earlier elections. The rule for widening the errors was "
           "committed before the first run: widen if fewer than 75% of the actual seat counts "
           "fall in their 80% intervals, or fewer than 90% in their 95% ones. Result: "
           f"{f['bt.in80']} and {f['bt.in95']}, so no widening (Figure 2).",
           "Ejecuté el mismo código siete días antes de las generales de noviembre de 2019 y "
           "de julio de 2023, calibrado solo con las anteriores. La regla para ensanchar los "
           "errores se fijó antes de empezar: si menos del 75 % de las listas cae en su "
           "horquilla del 80 %, o menos del 90 % en la del 95 %. Resultado: "
           f"{f['bt.in80']} y {f['bt.in95']}; no se ensanchan (figura 2)."))
    pg.table("(auto, auto, auto, auto)", "(left, center, center, center)",
             [L("Election, bloc", "Elección, bloque"), "P(≥ 176)",
              L("Actual\nseats", "Escaños\nreales"), L("Percentile", "Percentil")],
             [["2023, F", f["bt.2023.F.p"], f["bt.2023.F.actual"], f["bt.2023.F.pctile"]],
              ["2023, S", f["bt.2023.S.p"], f["bt.2023.S.actual"], f["bt.2023.S.pctile"]],
              [L("Nov 2019, S", "Noviembre de 2019, S"),
               f["bt.2019N.S.p"], f["bt.2019N.S.actual"], f["bt.2019N.S.pctile"]]],
             caption=L("Forecast P(≥ 176) and where the actual bloc total fell among the "
                       "simulated ones. S in 2019: PSOE, Unidas Podemos, PNV, Más País, BNG.",
                       "P(≥ 176) prevista y percentil del total real del bloque entre los "
                       "simulados. S en 2019: PSOE, Unidas Podemos, PNV, Más País y BNG."),
             n=1)
    lead, rule = s["backtest"]["at_2026_lead"], s["backtest"]["rule"]["targets"]
    short = [lvl for lvl, k in (("80", "cov80"), ("95", "cov95")) if lead[k] < rule[k]]
    if not short:
        verdict = L("both targets met", "se cumplen los dos objetivos")
    else:
        verdict = L(
            f"short of the {' and '.join(lvl + '%' for lvl in short)} target, so the 2026 "
            "intervals may be a little narrow",
            ("por debajo del objetivo del " if len(short) == 1 else
             "por debajo de los objetivos del ") + " y del ".join(f"{lvl} %" for lvl in short)
            + "; las horquillas de 2026 pueden quedarse algo estrechas")
    pg.p(L(f"Run {f['lead']} days out, as for 2026: {f['bt_lead.in80']} and "
           f"{f['bt_lead.in95']}, {verdict}.",
           f"A {f['lead']} días de la votación, como para 2026: {f['bt_lead.in80']} y "
           f"{f['bt_lead.in95']}, {verdict}."))
    return pg


def page_backtest_figure(s: dict, f: dict, L: Lang, out: Path, png: Path | None) -> Page:
    pg = Page(L)
    labels = draw("fig-backtests", s, f, L, out, png)
    pg.figure("fig-backtests.svg", 2, L(
        "Backtests: simulated 80% (thick) and 95% (thin) intervals and the actual seats "
        "(diamonds, filled when outside the 80% interval).",
        "Contraste: horquillas simuladas del 80 % (trazo grueso) y del 95 % (fino) y escaños "
        "reales (rombos, rellenos si quedan fuera de la del 80 %)."), labels)
    return pg


def page_seats(s: dict, f: dict, L: Lang, out: Path, png: Path | None) -> Page:
    pg = Page(L)
    pg.h(L("The 2026 parliament", "El Congreso de 2026"))
    labels = draw("fig-seats", s, f, L, out, png)
    pg.figure("fig-seats.svg", 3, L(
        f"Seats per list in {f['n']} simulated elections: mean (circle), 80% (thick) and 95% "
        "(thin) intervals.",
        f"Escaños por lista en {f['n']} elecciones simuladas: media (círculo) y horquillas "
        "del 80 % (grueso) y del 95 % (fino)."), labels)
    rows = []
    for b, name in (("F", "F"), ("S", "S"), ("S_no_JUNTS", L("S without Junts", "S sin Junts"))):
        rows.append([name, f[f"bloc.{b}.mean"], f[f"bloc.{b}.i80"], f[f"bloc.{b}.p"]])
    pg.table("(auto, auto, auto, auto)", "(left, center, center, center)",
             [L("Bloc", "Bloque"), L("Mean", "Media"), L("80% interval", "Horquilla 80 %"),
              "P(≥ 176)"], rows,
             caption=L("The two 2023 investiture blocs.",
                       "Los dos bloques de las investiduras de 2023."), n=2)
    return pg


def page_vote(s: dict, f: dict, L: Lang, out: Path, png: Path | None) -> Page:
    pg = Page(L)
    pg.h(L("What one vote is worth", "Cuánto vale un voto"))
    labels = draw("fig-constituencies", s, f, L, out, png)
    pg.figure("fig-constituencies.svg", 4, L(
        "The chance that one vote decides, for the average voter of each constituency. Log "
        "scales.",
        "Probabilidad de que un voto decida, para el votante medio de cada circunscripción. "
        "Escalas logarítmicas."), labels)
    top = f["seat.top1"]
    pg.p(L(f"Small constituencies weigh more: {f['eps.min']} electors per seat in "
           f"{f['eps.min.name']}, {f['eps.max']} in {f['eps.max.name']}. "
           f"{top}, {race(L, f[f'prov.{top}.seats'])}, is the most decisive: 1 in "
           f"{f['seat.top1.one_in']} for its seat, 1 in {f[f'prov.{top}.majority']} for the "
           f"majority. For the majority, {f['majority_any.bottom1']} is the least, at 1 in "
           f"{f['majority_any.bottom1.one_in']}.",
           f"Las circunscripciones pequeñas pesan más: {f['eps.min']} electores por escaño en "
           f"{f['eps.min.name']} y {f['eps.max']} en {f['eps.max.name']}. "
           f"{top}, {race(L, f[f'prov.{top}.seats'])}, es la más decisiva: 1 entre "
           f"{f['seat.top1.one_in']} para su escaño y 1 entre {f[f'prov.{top}.majority']} "
           "para la mayoría. Para la mayoría, la que menos es "
           f"{f['majority_any.bottom1']}, con 1 entre {f['majority_any.bottom1.one_in']}."))
    return pg


def page_power(s: dict, f: dict, L: Lang, out: Path, png: Path | None) -> Page:
    pg = Page(L)
    pg.h(L("Who holds the power", "Quién tiene el poder"))
    pg.p(L("Seats are not power. The Shapley–Shubik index is the share of the orders of "
           "forming a coalition in which a list's seats carry it to 176: arithmetic leverage, "
           "not who will govern.",
           "Tener escaños no es tener poder. El índice de Shapley–Shubik es la fracción de los "
           "órdenes de formar una coalición en los que los escaños de una lista la llevan a "
           "176: peso aritmético, no quién va a gobernar."))
    rows = []
    for p23, p26 in (("PP", "PP"), ("PSOE", "PSOE"), ("VOX", "VOX"), ("SUMAR", "FA"),
                     ("ERC", "ERC"), ("JUNTS", "JUNTS"), ("BILDU", "BILDU"), ("PNV", "PNV")):
        name = DISPLAY[p23] + (f" /\n{DISPLAY[p26]}" if p26 != p23 else "")
        rows.append([name, f[f"pw23.{p23}.seats"], f[f"pw23.{p23}.ss"], f[f"pw.{p26}.seats"],
                     f[f"pw.{p26}.ss"]])
    pg.table("(auto, auto, auto, auto, auto)", "(left, right, right, right, right)",
             [L("List", "Lista"), L("Seats\n2023", "Escaños\n2023"),
              L("Power\n2023", "Poder\n2023"), L("Seats\n2026", "Escaños\n2026"),
              L("Power\n2026", "Poder\n2026")], rows,
             caption=L("Seat share and Shapley–Shubik power; 2026, mean of the runs. Banzhaf "
                       "gives nearly the same (README).",
                       "Escaños y poder de Shapley–Shubik; 2026, media de las simulaciones. "
                       "El de Banzhaf da casi lo mismo (README)."), n=3)
    return pg


def page_why(s: dict, f: dict, L: Lang, out: Path, png: Path | None) -> Page:
    pg = Page(L)
    pg.h(L("Does voting pay?", "¿Compensa votar?"))
    pg.p(L("In the calculus of voting (Riker and Ordeshook, 1968), voting pays when",
           "Según el cálculo del voto (Riker y Ordeshook, 1968), votar compensa si"))
    pg.eq("R = p B - C + D > 0", 2)
    pg.p(L(f"with $p$ the chance of being decisive, $B$ what the outcome is worth to you, $C$ "
           f"the cost ({f['minutes']} minutes at {f['value_of_time']}: {f['cost']}) and $D$ "
           "what voting is worth in itself.",
           f"con $p$ la probabilidad de decidir, $B$ lo que vale para ti el resultado, $C$ el "
           f"coste ({f['minutes']} minutos a {f['value_of_time']}: {f['cost']}) y $D$ lo que "
           "vale votar en sí."))
    pg.p(L(f"With $p$ = 1 in {f['majority_any.one_in']}, a selfish voter breaks even only if "
           f"the majority is worth {f['th.majority.B']} to them (Downs, 1957).",
           f"Con $p$ = 1 entre {f['majority_any.one_in']}, a un votante egoísta solo le "
           f"compensa si para él la mayoría vale {f['th.majority.B']} (Downs, 1957)."))
    players = L("The players", "Los jugadores")
    pg.raw(f"#heading(level: 2, numbering: none)[{T(players)}]", players)
    pg.bullets([
        L("Voters: the outcome ($B$) and voting itself ($D$).",
          "Votantes: el resultado ($B$) y votar en sí ($D$)."),
        L("Parties: votes, office and policy (Strøm, 1990); their leverage is Table 3.",
          "Partidos: votos, cargos y políticas (Strøm, 1990); su peso, en la tabla 3."),
        L("Pollsters and media: they shape what each player expects of the others; no poll "
          "may be published in the five days before the vote (LOREG, art. 69.7).",
          "Encuestadoras y medios: forman lo que cada uno espera de los demás; no se "
          "publican encuestas los cinco días previos (LOREG, art. 69.7)."),
        L("Outside constraints, such as EU fiscal rules, narrow what any majority can do.",
          "Límites externos, como las reglas fiscales de la UE, acotan cualquier mayoría.")])
    return pg


def page_others(s: dict, f: dict, L: Lang, out: Path, png: Path | None) -> Page:
    pg = Page(L)
    pg.h(L("Counting the others", "Contando a los demás"))
    pg.p(L("If $B$ counts everyone (Edlin, Gelman and Kaplan, 2007),",
           "Si $B$ cuenta a todos (Edlin, Gelman y Kaplan, 2007),"))
    pg.eq("B = N b alpha", 3)
    pg.p(L(f"with $N$ = {f['population']} residents, $b$ the gain per person and $alpha$ the "
           f"weight you give a stranger. Here $p N$ = {f['th.majority.pN']}: with $b$ = 100 €, "
           f"voting pays once $alpha$ passes {f['th.majority.alpha100']}, about 1 in "
           f"{f['th.majority.inv_alpha100']}.",
           f"con $N$ = {f['population']} de residentes, $b$ lo que gana cada persona y $alpha$ "
           f"el peso que das a un desconocido. Aquí $p N$ = {f['th.majority.pN']}: con $b$ = "
           f"100 €, votar compensa cuando $alpha$ pasa del {f['th.majority.alpha100']}, más o "
           f"menos 1 entre {f['th.majority.inv_alpha100']}."))
    labels = draw("fig-break-even", s, f, L, out, png)
    pg.figure("fig-break-even.svg", 5, L(
        f"Above each line, $p N b alpha$ exceeds the {f['cost']} cost; the circle is $b$ = "
        "100 €.",
        f"Por encima de cada línea, $p N b alpha$ supera el coste de {f['cost']}; el círculo "
        "es $b$ = 100 €."), labels)
    return pg


def page_limits(s: dict, f: dict, L: Lang, out: Path, png: Path | None) -> Page:
    pg = Page(L)
    pg.h(L("Others' votes, limits, takeaways", "Movilizar, límites y conclusiones"))
    pg.run_in(L("Others' votes.", "Movilizar."), L(
        "Persuasion barely moves votes in general elections (Kalla and Broockman, 2018); "
        "getting people out does, in US experiments (Gerber, Green and Larimer, 2008). At an "
        f"assumed {f['vph_lo']} to {f['vph_hi']} extra voters per hour, an hour beats "
        f"{f['value_of_time']} only if the majority is worth {f['th.majority.infl1.0']} to "
        f"{f['th.majority.infl0.1']} to you, or on the social reckoning of (3).",
        "Convencer apenas mueve votos en unas generales (Kalla y Broockman, 2018); movilizar "
        f"sí, en experimentos en {USA} (Gerber, Green y Larimer, 2008). Suponiendo de "
        f"{f['vph_lo']} a {f['vph_hi']} votantes más por hora, una hora movilizando vale más "
        f"que {f['value_of_time']} solo si la mayoría vale para ti entre "
        f"{f['th.majority.infl1.0']} y {f['th.majority.infl0.1']}, o con la cuenta social "
        "de (3)."))
    pg.run_in(L("Limits.", "Límites."), L(
        f"Polls {f['lead']} days out. Proportional swing; SALF and Adelante Andalucía rest on "
        "the 2024 European vote or a flat share. Local lists can surprise. Blocs fixed by "
        "the 2023 votes.",
        f"Encuestas a {f['lead']} días. Cambio proporcional; SALF y Adelante Andalucía se "
        "apoyan en las europeas de 2024 o en un porcentaje fijo. Las listas locales pueden "
        "sorprender. Bloques fijados por las votaciones de 2023."))
    pg.run_in(L("Takeaways.", "Conclusiones."), L(
        "A seat is a far likelier prize than the majority. Between constituencies, the odds "
        f"of deciding the majority differ by a factor of up to {f['majority_any.spread']}. "
        "Selfishly, voting rarely pays; counting others, it can.",
        "Un escaño es un premio mucho más probable que la mayoría. Entre circunscripciones, "
        f"la probabilidad de decidir la mayoría varía hasta {f['majority_any.spread']} veces. "
        "Por interés propio, votar rara vez compensa; contando a los demás, puede compensar."))
    pg.raw(f"#v(0.6em)\n#align(center, strong[{T(REPO)}])", REPO)
    return pg


def page_references(s: dict, f: dict, L: Lang, out: Path, png: Path | None) -> Page:
    pg = Page(L)
    title = L.meta["references"]
    pg.raw(f"#heading(numbering: none)[{T(title)}]", title)
    refs, plain = [], []
    for authors, year, title_, where, book in REFERENCES:
        if book:
            typ = f"{T(authors)} ({year}). #emph[{T(title_)}] {T(where)}."
        else:
            typ = f"{T(authors)} ({year}). {T(title_)} #emph[{T(where)}]."
        refs.append(f"[{typ}]")
        plain.append(f"{authors} ({year}). {title_} {where}.")
    pg.raw("#block({\n  set par(justify: false, hanging-indent: 1em, spacing: 0.62em)\n  "
           + "\n  parbreak()\n  ".join(refs) + "\n})")
    pg.refs = plain
    return pg


def make_figures(results_dir: Path, figures_dir: Path, lang: str = "en") -> None:
    """The five figures alone, as PNG and SVG, for the README."""
    style.paper_style()
    summary = style.load_summary(results_dir)
    L, f = Lang(lang), fx.build(summary, lang)
    out = Path(figures_dir)
    out.mkdir(parents=True, exist_ok=True)
    for name in FIGURES:
        draw(name, summary, f, L, out, out)
        print(f"-> {out / name}.png")


PAGES = [page_title, page_question, page_model, page_decisive, page_backtest,
         page_backtest_figure, page_seats, page_vote, page_power, page_why, page_others,
         page_limits, page_references]


def typst_source(L: Lang, pages: list[Page]) -> str:
    m = L.meta
    sizes = {"@PAGE_W": lg.PAGE_W_IN, "@PAGE_H": lg.PAGE_H_IN, "@MARGIN_X": MARGIN_X,
             "@BODY": lg.BODY_PT, "@ITALIC": lg.ITALIC_PT, "@HEADING": lg.HEADING_PT}
    source = PREAMBLE
    for key, value in sizes.items():
        source = source.replace(key, f"{value:g}")
    source = (source.replace("@TITLE", m["title"]).replace("@AUTHOR", AUTHOR)
              .replace("@HEADER", T(f"{m['title']} · {AUTHOR}")).replace("@LANG", m["typst"])
              .replace("@NAMES", r"\b(?:" + "|".join(NAMES) + r")\b"))
    return source + "\n" + "\n\n#pagebreak()\n\n".join(pg.markup() for pg in pages) + "\n"


def make_carousel(results_dir: Path, carousel_dir: Path, figures_dir: Path | None = None,
                  lang: str = "es") -> None:
    """The carousel in one language: carousel.pdf, slide-NN.png and slides.txt in
    carousel_dir; PNG copies of the figures in figures_dir, if given."""
    logging.getLogger("fontTools").setLevel(logging.ERROR)
    style.paper_style()
    summary = style.load_summary(results_dir)
    L, f = Lang(lang), fx.build(summary, lang)
    out = Path(carousel_dir)
    out.mkdir(parents=True, exist_ok=True)
    if figures_dir is not None:
        Path(figures_dir).mkdir(parents=True, exist_ok=True)
    for old in [*out.glob("slide-*.png"), *out.glob("fig-*.svg")]:
        old.unlink()
    pages = [make(summary, f, L, out, figures_dir) for make in PAGES]
    typ = out / "carousel.typ"
    typ.write_text(typst_source(L, pages))
    common = {"root": str(out), "font_paths": [str(style.FONTS)], "ignore_system_fonts": True}
    pdf_path = out / "carousel.pdf"
    typst.compile(str(typ), output=str(pdf_path), **common)
    ppi = lg.PREVIEW_PX / lg.PAGE_W_IN
    typst.compile(str(typ), output=str(out / "slide-{p}.png"), format="png", ppi=ppi, **common)
    pngs = sorted(out.glob("slide-*.png"), key=lambda p: int(re.search(r"\d+", p.name)[0]))
    for i, png in enumerate(pngs, start=1):
        png.rename(out / f"slide-{i:02d}.png")
    if len(pngs) != len(PAGES):
        print(f"  warning: {len(pngs)} pages for {len(PAGES)} slides: something overflows")
    m = L.meta
    text = [f"## {m['slide']} {i}\n\n" + "\n\n".join(t for t in pg.txt if t.strip())
            for i, pg in enumerate(pages[:-1], start=1)]
    (out / "slides.txt").write_text("\n\n".join(text) + f"\n\n## {m['references']}\n\n" +
                                    "\n".join(pages[-1].refs) + "\n")
    bad = lg.pdf_violations(pdf_path)
    if bad:
        raise ValueError(f"{pdf_path}: {len(bad)} glyphs break the type floor, e.g. {bad[:5]}")
    print(f"-> {pdf_path} ({len(pngs)} pages), {out / 'slides.txt'}")
