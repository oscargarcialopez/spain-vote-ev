"""The LinkedIn carousel: nine 4:5 pages (6 x 7.5 in, previews at 1080 x 1350 px) set like a
paper, in Spanish (carousel/, the one published) or English (carousel/en/). STIX Two type
(vendored in fonts/), numbered sections and equations, captioned figures, ruled tables and the
references; black and greys and one brown accent that is no party's colour. Typst sets the
pages and matplotlib draws the figures as SVG (English PNG copies go to figures/ for the README).

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

from . import facts as fx
from . import style, theory
from .parties import DISPLAY
from .style import ACCENT, FILL, GREY, INK, plt

AUTHOR = "Óscar García López"
REPO = "github.com/oscargarcialopez/spain-vote-ev"
TEXT_W = 4.9  # inches: a 6 in page with 0.55 in margins
NB = fx.NBSP
USA = f"EE.{NB}UU."

META = {
    "en": {"title": "What is one vote worth?",
           "subtitle": "Spain's general election of 29 November 2026",
           "short": "What is one vote worth? Spain, 29 November 2026",
           "date": "November 2026", "abstract": "Abstract", "figure": "Figure",
           "table": "Table", "slide": "Slide", "references": "References",
           "typst": 'lang: "en", region: "gb"'},
    "es": {"title": "¿Cuánto vale un voto?",
           "subtitle": "Las elecciones generales del 29 de noviembre de 2026",
           "short": "¿Cuánto vale un voto? Generales del 29 de noviembre de 2026",
           "date": "Noviembre de 2026", "abstract": "Resumen", "figure": "Figura",
           "table": "Tabla", "slide": "Diapositiva", "references": "Referencias",
           "typst": 'lang: "es", region: "ES"'},
}

# Kept in English, with their original titles, in both carousels.
REFERENCES = [
    ("Arrow, K. J. (1951).", "Social Choice and Individual Values.", "Wiley."),
    ("Banzhaf, J. F. (1965). Weighted voting doesn't work.", "Rutgers Law Review",
     "19(2), 317–343."),
    ("Downs, A. (1957).", "An Economic Theory of Democracy.", "Harper."),
    ("Edlin, A., Gelman, A., & Kaplan, N. (2007). Voting as a rational choice.",
     "Rationality and Society", "19(3), 293–314."),
    ("Gelman, A., Silver, N., & Edlin, A. (2012). What is the probability your vote will make "
     "a difference?", "Economic Inquiry", "50(2), 321–326."),
    ("Gerber, A. S., Green, D. P., & Larimer, C. W. (2008). Social pressure and voter turnout.",
     "American Political Science Review", "102(1), 33–48."),
    ("Gibbard, A. (1973). Manipulation of voting schemes.", "Econometrica", "41(4), 587–601."),
    ("Kalla, J. L., & Broockman, D. E. (2018). The minimal persuasive effects of campaign "
     "contact in general elections.", "American Political Science Review", "112(1), 148–166."),
    ("Riker, W. H., & Ordeshook, P. C. (1968). A theory of the calculus of voting.",
     "American Political Science Review", "62(1), 25–42."),
    ("Satterthwaite, M. A. (1975). Strategy-proofness and Arrow's conditions.",
     "Journal of Economic Theory", "10(2), 187–217."),
    ("Shapley, L. S., & Shubik, M. (1954). A method for evaluating the distribution of power "
     "in a committee system.", "American Political Science Review", "48(3), 787–792."),
    ("Strøm, K. (1990). A behavioral theory of competitive political parties.",
     "American Journal of Political Science", "34(2), 565–598."),
]

PREAMBLE = r"""
#set document(title: "@TITLE", author: "@AUTHOR", date: none)
#set page(
  width: 6in, height: 7.5in,
  margin: (x: 0.55in, top: 0.74in, bottom: 0.62in),
  header: context if here().page() > 1 {
    set text(9.5pt, style: "italic")
    grid(columns: (1fr, auto), [@SHORT], [@AUTHOR])
    v(-3pt)
    line(length: 100%, stroke: 0.4pt)
  },
  footer: context align(center, text(10pt)[#here().page()]),
)
#set text(font: "STIX Two Text", size: 13pt, @LANG)
#show regex("@NAMES"): set text(hyphenate: false)
#show math.equation: set text(font: "STIX Two Math")
#set par(justify: true, leading: 0.5em, spacing: 0.75em)
#set heading(numbering: "1.")
#show heading: set text(15pt, weight: "bold")
#show heading: set block(above: 0pt, below: 0.75em)
#show heading.where(level: 2): set text(12.5pt)
#show heading.where(level: 2): set block(above: 1.0em, below: 0.55em)
#set math.equation(numbering: "(1)")
#set enum(indent: 0.4em, body-indent: 0.6em, spacing: 0.5em)
#set list(indent: 0.4em, body-indent: 0.6em, spacing: 0.5em, marker: [•])
#show list: set par(justify: false)
#show enum: set par(justify: false)
#let cap(kind, n, body, above: 0.5em) = block(above: above, below: 0.8em, {
  set text(11pt)
  set par(justify: true, leading: 0.42em)
  [#strong[#kind #n.] #body]
})
#let ruled(cols, aligns, header, ..rows) = align(center, {
  set text(11pt)
  set par(justify: false)
  table(
    columns: cols, align: aligns, stroke: none, inset: (x: 4.5pt, y: 3.2pt),
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
# Authors' names are not hyphenated.
NAMES = sorted({n for lead, _, _ in REFERENCES for n in re.findall(r"([A-Z][\w']+), [A-Z]\.",
                                                                  lead)})


class Lang:
    """A page's language: L(english, spanish) picks one; Spanish text gets its no-break
    spaces."""

    def __init__(self, code: str):
        if code not in META:
            raise ValueError(f"unknown language {code!r}")
        self.code, self.es, self.meta = code, code == "es", META[code]

    def __call__(self, en, es):
        if not self.es:
            return en
        if not isinstance(es, str):
            return es
        return UNBROKEN_ES.sub(lambda m: m.group().replace(" ", NB), es)


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
         "dot": "·", "times": "×"}


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
        out.append(p.replace('"', "").replace("_", "").replace("  ", " "))
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

    def eq(self, math: str, plain: str) -> None:
        self.raw(f"$ {math} $", plain)

    def bullets(self, srcs: list[str]) -> None:
        self.raw("\n".join(f"- {T(s)}" for s in srcs), [P(s) for s in srcs])

    def figure(self, name: str, n: int, caption: str, labels: list[str]) -> None:
        kind = self.L.meta["figure"]
        self.raw(f'#align(center, image("{name}"))\n#cap("{kind}", {n})[{T(caption)}]',
                 [f"{kind} {n}. {P(caption)}"] + labels)

    def table(self, cols: str, aligns: str, header: list[str], rows: list[list[str]],
              caption: str | None = None, n: int | None = None) -> None:
        cells = ", ".join(cell(x) for r in rows for x in r)
        typ = f"#ruled({cols}, {aligns}, ({', '.join(cell(h) for h in header)},), {cells})"
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


def texts(fig) -> list[str]:
    """The words on a figure that are not tick numbers, with $math$ as plain letters."""
    out = []
    for ax in fig.axes:
        out += [t.get_text() for t in ax.texts]
        out += [ax.get_xlabel(), ax.get_ylabel()]
        for t in [*ax.get_yticklabels(), *ax.get_xticklabels()]:
            if re.search("[A-Za-z]", t.get_text()):
                out.append(t.get_text())
        if ax.get_legend():
            out += [t.get_text() for t in ax.get_legend().get_texts()]
    out = [re.sub(r"\$\\?(\w+)\$", lambda m: GREEK.get(m[1], m[1]), t) for t in out]
    return [t.replace("\n", " ") for t in out if t.strip()]


def save(fig, svg: Path, png: Path | None) -> list[str]:
    labels = texts(fig)
    fig.savefig(svg, format="svg", bbox_inches="tight", pad_inches=0.03,
                metadata={"Date": None})
    if png is not None:
        fig.savefig(png, format="png", dpi=200, bbox_inches="tight", pad_inches=0.05,
                    metadata={"Software": None})
    plt.close(fig)
    return labels


ODDS_TICKS = {"en": [(1e3, "1,000"), (1e5, "100,000"), (1e7, "10 million"), (1e9, "1 billion")],
              "es": [(1e3, "1.000"), (1e5, "100.000"), (1e7, "10 millones"),
                     (1e9, "1.000 millones")]}


def fig_odds(s: dict, f: dict, L: Lang, svg: Path, png: Path | None) -> list[str]:
    nat = s["vote"]["national"]
    rows = [(L("one vote changes a seat", "un voto cambia un escaño"),
             nat["seat"]["one_in"], f["seat.one_in"], True),
            (L("one vote changes whether a bloc has 176 seats",
               "un voto decide si un bloque llega a 176 escaños"),
             nat["majority_any"]["one_in"], f["majority_any.one_in"], True),
            (L("picking all six numbers of 49", "acertar los seis números de la Primitiva"),
             fx.LOTTERY, f["lottery"], False),
            (L("one vote decides the 2008 US presidency",
               f"un voto decide las presidenciales de {USA} de 2008"),
             s["context"]["gse_2012_one_in"], f["gse"], False)]
    fig, ax = plt.subplots(figsize=(TEXT_W, 2.15))
    for k, (label, val, txt, ours) in enumerate(rows):
        y = -k
        ax.barh(y, val - 300, left=300, height=0.36, color=INK if ours else "white",
                edgecolor=INK, hatch=None if ours else "////", lw=0.6)
        ax.text(360, y + 0.25, label, fontsize=10.5, va="bottom")
        ax.text(val * 1.45, y, f"{L('1 in', '1 entre')} {txt}", fontsize=10.5, va="center")
    ax.set_xscale("log")
    ax.set_xlim(300, L(1e10, 4e10))
    ax.set_ylim(-len(rows) + 0.55, 0.9)
    ax.set_yticks([])
    ticks = ODDS_TICKS[L.code]
    ax.set_xticks([t for t, _ in ticks], [lab for _, lab in ticks], fontsize=10)
    ax.minorticks_off()
    ax.set_xlabel(L("odds, 1 in N (log scale)", "probabilidad, 1 entre N (escala logarítmica)"),
                  fontsize=11)
    return save(fig, svg, png)


ELECTION_NAME = {"en": {"2019N": "November 2019", "2023": "July 2023"},
                 "es": {"2019N": "Noviembre de 2019", "2023": "Julio de 2023"}}


def fig_backtests(s: dict, f: dict, L: Lang, svg: Path, png: Path | None) -> list[str]:
    runs = s["backtest"]["runs"]
    fig, axes = plt.subplots(1, len(runs), figsize=(TEXT_W, 2.05))
    top = max(x["hi95"] for run in runs for x in run["lists"])
    for ax, run in zip(axes, runs, strict=True):
        rows = sorted((x for x in run["lists"] if x["counted"]), key=lambda x: x["actual"])
        for y, x in enumerate(rows):
            ax.plot([x["lo95"], x["hi95"]], [y, y], color=INK, lw=0.7, solid_capstyle="butt",
                    clip_on=False)
            ax.plot([x["lo80"], x["hi80"]], [y, y], color=INK, lw=2.6,
                    solid_capstyle="projecting", clip_on=False)
            ax.plot([x["actual"]], [y], "D", ms=3.6, mec=ACCENT, mew=0.9,
                    mfc="white" if x["in80"] else ACCENT, clip_on=False, zorder=4)
        ax.set_xscale("function", functions=(lambda v: np.sqrt(np.clip(v, 0, None)), np.square))
        ax.set_xlim(0, top * 1.08)
        ax.set_xticks([0, 1, 5, 20, 50, 100, 150], ["0", "1", "5", "20", "50", "100", "150"],
                      fontsize=8.5)
        ax.minorticks_off()
        ax.set_yticks(range(len(rows)), [DISPLAY.get(x["list"], x["list"]) for x in rows],
                      fontsize=8.5)
        ax.tick_params(axis="y", length=0)
        ax.set_ylim(-0.7, len(rows) - 0.3)
        ax.set_title(ELECTION_NAME[L.code][run["election"]], fontsize=9.5, pad=3)
        ax.set_xlabel(L("seats (square-root scale)", "escaños (escala de raíz cuadrada)"),
                      fontsize=9.5)
    fig.subplots_adjust(wspace=0.55)
    return save(fig, svg, png)


def fig_seats(s: dict, f: dict, L: Lang, svg: Path, png: Path | None) -> list[str]:
    lists = [(k, v) for k, v in s["lists"].items() if v["mean"] >= 0.5]
    lists.sort(key=lambda kv: kv[1]["mean"])
    fig, ax = plt.subplots(figsize=(TEXT_W, 2.75))
    for y, (_, v) in enumerate(lists):
        ax.plot([v["lo95"], v["hi95"]], [y, y], color=INK, lw=0.8, solid_capstyle="butt")
        ax.plot([v["lo80"], v["hi80"]], [y, y], color=INK, lw=3.2, solid_capstyle="butt")
        ax.plot([v["mean"]], [y], "o", ms=4.6, mfc="white", mec=INK, mew=0.9)
    ax.set_yticks(range(len(lists)), [v["name"] for _, v in lists], fontsize=10.5)
    ax.set_xlim(0, 180)
    ax.set_ylim(-0.6, len(lists) - 0.4)
    ax.set_xlabel(L("seats", "escaños"), fontsize=11)
    ax.tick_params(axis="y", length=0)
    return save(fig, svg, png)


ODDS_TICKS_Y = {"en": ["10,000", "100,000", "1 million", "10 million", "100 million"],
                "es": ["10.000", "100.000", "1 millón", "10 millones", "100 millones"]}
# Where a label may go around its point, nearest first: offsets in points, alignment.
LABEL_SPOTS = [(dx * r, dy * r, ha, va) for r in (1, 2, 3)
               for dx, dy, ha, va in ((5, 0, "left", "center"), (-5, 0, "right", "center"),
                                      (0, 5, "center", "bottom"), (0, -5, "center", "top"),
                                      (4, 4, "left", "bottom"), (-4, 4, "right", "bottom"),
                                      (4, -4, "left", "top"), (-4, -4, "right", "top"))]
MARKER_PT = 3.8  # marker diameter of the constituency figure, in points


def point_boxes(ax, xy: np.ndarray, size_pt: float = MARKER_PT) -> list:
    """The display-space box of every marker."""
    from matplotlib.transforms import Bbox
    r = size_pt / 2 * ax.figure.dpi / 72 + 1
    return [Bbox.from_extents(x - r, y - r, x + r, y + r) for x, y in ax.transData.transform(xy)]


def place_labels(ax, items: list[tuple[str, tuple[float, float]]], points: np.ndarray,
                 fontsize: float = 9.5) -> list:
    """Each (text, point) label at the nearest spot around its point where it stays inside
    the axes and overlaps no marker, no other label and the legend."""
    fig = ax.figure
    fig.canvas.draw()
    rend = fig.canvas.get_renderer()
    frame = ax.get_window_extent(rend)
    taken = point_boxes(ax, points)
    if ax.get_legend():
        taken.append(ax.get_legend().get_window_extent(rend))
    out = []
    for text, xy in items:
        for dx, dy, ha, va in LABEL_SPOTS:
            far = abs(dx) + abs(dy) > 10
            t = ax.annotate(text, xy, xytext=(dx, dy), textcoords="offset points", ha=ha,
                            va=va, fontsize=fontsize, color=GREY,
                            arrowprops={"arrowstyle": "-", "lw": 0.5, "color": GREY,
                                        "shrinkA": 0, "shrinkB": 2.5} if far else None)
            box = t.get_window_extent(rend).padded(1)
            inside = (box.x0 >= frame.x0 and box.x1 <= frame.x1 and box.y0 >= frame.y0
                      and box.y1 <= frame.y1)
            if inside and not any(box.overlaps(b) for b in taken):
                taken.append(box)
                out.append(t)
                break
            t.remove()
        else:
            raise ValueError(f"no room for the label {text!r}")
    return out


def extremes(prov: list[dict], events: tuple[str, ...]) -> list[tuple[str, int]]:
    """The most and the least decisive constituency of each event: (event, index)."""
    out = []
    for ev in events:
        vals = [r[f"one_in_{ev}"] for r in prov]
        out += [(ev, int(np.argmin(vals))), (ev, int(np.argmax(vals)))]
    return out


def draw_constituencies(s: dict, L: Lang):
    """Figure 4 and what its test needs: the axes, the markers' positions and the labels."""
    prov = s["vote"]["provinces"]
    ev2 = "government" if "one_in_government" in prov[0] else "majority_any"
    seats = np.array([r["seats"] for r in prov], float)
    x = seats * (1 + 0.035 * (np.arange(len(prov)) % 3 - 1))
    y = {ev: np.array([r[f"one_in_{ev}"] for r in prov]) for ev in ("seat", ev2)}
    fig, ax = plt.subplots(figsize=(TEXT_W, 2.7))
    ax.plot(x, y["seat"], "o", ms=3.6, mfc=INK, mec=INK, mew=0.5,
            label=L("changes a seat", "cambia un escaño"))
    ax.plot(x, y[ev2], "o", ms=MARKER_PT, mfc="white", mec=ACCENT, mew=0.9,
            label=L("changes who is invested", "cambia quién es investido")
            if ev2 == "government" else
            L("changes whether a bloc has 176", "decide si un bloque llega a 176"))
    ax.set_xscale("log")
    ax.set_yscale("log")
    top = int(seats.max())
    ax.set_xlim(0.8, top * 1.35)
    lo = min(y["seat"].min(), y[ev2].min())
    hi = max(y["seat"].max(), y[ev2].max())
    ax.set_ylim(10 ** np.floor(np.log10(lo) - 0.3), 10 ** np.ceil(np.log10(hi) + 0.3))
    ax.set_xticks([1, 2, 5, 10, 20, top], ["1", "2", "5", "10", "20", str(top)])
    ax.minorticks_off()
    ticks = [t for t in (1e4, 1e5, 1e6, 1e7, 1e8) if ax.get_ylim()[0] <= t <= ax.get_ylim()[1]]
    ax.set_yticks(ticks, [ODDS_TICKS_Y[L.code][int(np.log10(t)) - 4] for t in ticks],
                  fontsize=9.5)
    ax.set_xlabel(L("seats in the constituency (log scale)",
                    "escaños de la circunscripción (escala logarítmica)"), fontsize=11)
    ax.set_ylabel(L("odds, 1 in N", "probabilidad, 1 entre N"), fontsize=11)
    ax.legend(loc="best", fontsize=9.5, handletextpad=0.3, borderpad=0.4)
    points = np.vstack([np.column_stack([x, y[ev]]) for ev in ("seat", ev2)])
    items = [(prov[i]["name"], (x[i], y[ev][i])) for ev, i in extremes(prov, ("seat", ev2))]
    labels = place_labels(ax, items, points)
    return fig, ax, points, labels


def fig_constituencies(s: dict, f: dict, L: Lang, svg: Path, png: Path | None) -> list[str]:
    fig, *_ = draw_constituencies(s, L)
    return save(fig, svg, png)


def fig_break_even(s: dict, f: dict, L: Lang, svg: Path, png: Path | None) -> list[str]:
    th = s["theory"]
    b = theory.B_GRID
    fig, ax = plt.subplots(figsize=(TEXT_W, 2.55))
    a_maj = theory.break_even_alpha(th["majority"]["p"], th["population"], b)
    a_seat = theory.break_even_alpha(th["seat"]["p"], th["population"], b)
    maj = L("majority: $p$ = 1 in ", "mayoría: $p$ = 1 entre ") + f["majority_any.one_in"]
    seat = L("a seat: $p$ = 1 in ", "un escaño: $p$ = 1 entre ") + f["seat.one_in"]
    ax.fill_between(b, a_maj, 1, color=FILL, lw=0)
    ax.plot(b, a_maj, color=INK, lw=1.1, label=maj)
    ax.plot(b, a_seat, color=GREY, lw=1.0, ls="--", label=seat)
    ax.plot([100], [th["majority"]["alpha_for_b_100"]], "o", ms=4.5, mfc="white", mec=ACCENT,
            mew=1.0)
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlim(1, 1e5)
    ax.set_ylim(1e-6, 1)
    ax.set_xticks([1, 10, 100, 1e3, 1e4, 1e5],
                  ["1", "10", "100"] + L(["1,000", "10,000", "100,000"],
                                         ["1.000", "10.000", "100.000"]))
    ax.set_yticks([1e-6, 1e-4, 1e-2, 1], L(["0.0001%", "0.01%", "1%", "100%"],
                                          [f"0,0001{NB}%", f"0,01{NB}%", f"1{NB}%",
                                           f"100{NB}%"]))
    ax.minorticks_off()
    ax.text(20, 0.15, L("voting pays (majority)", "votar compensa (mayoría)"), fontsize=10.5)
    ax.set_xlabel(L("$b$, gain per person from the outcome (€)",
                    "$b$, lo que gana cada persona con el resultado (€)"), fontsize=11)
    ax.set_ylabel(L("$\\alpha$, weight on others", "$\\alpha$, peso de los demás"), fontsize=11)
    for p, at, up, text in ((th["majority"]["p"], 300, 2.4, maj),
                            (th["seat"]["p"], 2.2, 1 / 3.2, seat)):
        y = theory.break_even_alpha(p, th["population"], np.array([at]))[0]
        a, b2 = ax.transData.transform((at, y)), ax.transData.transform((at * 10, y / 10))
        angle = float(np.degrees(np.arctan2(b2[1] - a[1], b2[0] - a[0])))
        ax.text(at, y * up, text, fontsize=9.5, rotation=angle, rotation_mode="anchor",
                color=INK if up > 1 else GREY)
    return save(fig, svg, png)


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
    pg.raw("#align(center)[\n  #v(2pt)\n"
           f"  #text(21pt, weight: \"bold\", hyphenate: false)[{T(m['title'])}]\n  #v(2pt)\n"
           f"  #text(14.5pt, style: \"italic\")[{T(m['subtitle'])}]\n  #v(8pt)\n"
           f"  #text(13pt)[{T(AUTHOR)}]\n  #v(-2pt)\n  #text(11.5pt)[{T(m['date'])}]\n]",
           [m["title"], m["subtitle"], AUTHOR, m["date"]])
    maj = s["vote"]["national"]["majority_any"]["one_in"]
    gse, lottery = s["context"]["gse_2012_one_in"] / maj, fx.LOTTERY / maj
    abstract = L(
        f"I simulate Spain's election {f['n']} times from the polls to {nb(f['cutoff'])}, "
        "constituency by constituency, with errors measured on the same poll summary in "
        "past elections. For the average voter, one more vote changes a seat with probability "
        f"1 in {f['seat.one_in']}, and changes whether either 2023 investiture bloc reaches 176 "
        f"seats with probability 1 in {f['majority_any.one_in']}: "
        + compare(L, gse, f["ratio_gse"], "deciding the 2008 US presidency") + ", and "
        + compare(L, lottery, None, "picking all six numbers of 49")
        + ". The numbers treat every list alike and advise no one.",
        f"Simulo {f['n']} veces las elecciones, circunscripción a circunscripción, con la "
        f"mediana de las encuestas hasta el {f['cutoff']} y los errores que tuvo en "
        "elecciones pasadas. Para el votante medio, un voto más cambia un escaño con una "
        f"probabilidad de 1 entre {f['seat.one_in']} y decide si uno de los bloques de las "
        "investiduras de 2023 llega a 176 escaños con una de 1 entre "
        f"{f['majority_any.one_in']}, "
        + compare(L, gse, f["ratio_gse"], f"decidir las presidenciales de {USA} de 2008")
        + " y " + compare(L, lottery, None, "acertar los seis números de la Primitiva")
        + ". El cálculo trata igual a todas las listas y no aconseja nada a nadie.")
    pg.raw("#v(4pt)\n"
           f"#align(center, text(12.5pt, weight: \"bold\")[{m['abstract']}])\n#v(-3pt)\n"
           f"#pad(x: 1.0em)[#set text(12pt)\n#set par(leading: 0.45em)\n{T(abstract)}]",
           [m["abstract"], P(abstract)])
    labels = fig_odds(s, f, L, out / "fig-odds.svg", png and png / "fig-odds.png")
    pg.raw("#v(2pt)")
    pg.figure("fig-odds.svg", 1, L(
        "How likely one vote is to decide. Black: this model, average Spanish voter. Hatched: "
        "references (Gelman, Silver and Edlin, 2012).",
        "Probabilidad de que un voto decida. Barras negras: este modelo, votante medio de "
        "España. Rayadas: referencias (Gelman, Silver y Edlin, 2012)."), labels)
    note = L("Code, data and method: linked in the first comment.",
             "Código, datos y método: enlace en el primer comentario.")
    pg.raw("#v(1fr)\n#block(width: 100%, {\n  line(length: 30%, stroke: 0.4pt)\n  v(-2pt)\n"
           f"  text(10.5pt)[{T(note)}]\n}})", P(note))
    return pg


def yes(f: dict, who: str, parties: list[tuple[str, str]]) -> str:
    """'PP 137, Vox 33, …', each name with its number on one line."""
    return ", ".join(f"{name.replace(' ', NB)}{NB}{f[f'{who}.{code}']}" for name, code in parties)


def page_question(s: dict, f: dict, L: Lang, out: Path, png: Path | None) -> Page:
    pg = Page(L)
    pg.h(L("The question", "La pregunta"))
    pg.p(L("A vote matters when it changes something. Spain elects 350 deputies in 52 "
           "constituencies by D'Hondt, with a 3% threshold in each; Ceuta and Melilla elect "
           "one each. One more vote can move a seat from one list to another, or move the seat "
           "that decides a majority of 176.",
           "Un voto importa cuando cambia algo. España elige 350 diputados en 52 "
           "circunscripciones con la ley D'Hondt y un umbral del 3 % en cada una; Ceuta y "
           "Melilla eligen uno cada una. Un voto más puede pasar un escaño de una lista a "
           "otra, o mover el escaño que decide una mayoría absoluta de 176."))
    pg.p(L("For the majority I use the coalitions of the two 2023 investiture votes, so no "
           "party is placed by anyone's judgement:",
           "Para la mayoría uso los bloques de las dos votaciones de investidura de 2023; así "
           "nadie decide a mano dónde va cada partido:"))
    fe, sa = "inv.feijoo", "inv.sanchez"
    pg.table("(auto, auto, 1fr)", "(left, left, left)",
             [L("Bloc", "Bloque"), L("Vote", "Votación"), L("Yes votes", "Votos a favor")], [
        ["F", L(f"Feijóo, 27 Sep 2023: {f[fe + '.yes']}",
                f"Feijóo,\n27 de septiembre de 2023: {f[fe + '.yes']}"),
         yes(f, fe, [("PP", "PP"), ("Vox", "VOX"), ("UPN", "UPN"), ("CC", "CC")])],
        ["S", L(f"Sánchez, 16 Nov 2023: {f[sa + '.yes']}",
                f"Sánchez,\n16 de noviembre de 2023: {f[sa + '.yes']}"),
         yes(f, sa, [("PSOE", "PSOE"), ("Sumar", "SUMAR"), ("ERC", "ERC"), ("Junts", "JUNTS"),
                     ("EH Bildu", "BILDU"), ("PNV", "PNV"), ("BNG", "BNG"), ("CC", "CC")])]])
    pg.p(L("Frente Amplio and Podemos, both in Sumar's group in 2023, count in S; lists with "
           "no seat in 2023 count in neither; Coalición Canaria voted yes twice, so it is in "
           "both. I also report S without Junts.",
           "Frente Amplio y Podemos, que en 2023 estaban en el grupo de Sumar, cuentan en S; "
           "las listas sin escaño en 2023 no cuentan en ninguno; Coalición Canaria votó sí las "
           "dos veces, así que está en los dos. También doy S sin Junts."))
    pg.p(L("Whether voting pays is the calculus of voting (Riker and Ordeshook, 1968):",
           "Si votar compensa o no es el cálculo del voto (Riker y Ordeshook, 1968):"))
    pg.eq("R = p B - C + D", "R = pB − C + D (1)")
    pg.p(L("where $p$ is the chance of being decisive, $B$ what the outcome is worth to you, "
           "$C$ the cost of voting and $D$ what voting is worth in itself. This study "
           "estimates $p$.",
           "donde $p$ es la probabilidad de que tu voto decida, $B$ lo que vale para ti el "
           "resultado, $C$ el coste de votar y $D$ lo que vale votar en sí. Este estudio "
           "estima $p$."))
    return pg


def page_model(s: dict, f: dict, L: Lang, out: Path, png: Path | None) -> Page:
    pg = Page(L)
    pg.h(L("The model", "El modelo"))
    party = "" if f["party_released"] in ("none", "ninguna") else L(
        f" One poll in the window was released by a party ({f['party_released']}); without "
        f"it, $P(F >= 176)$ is {f['sens.F.p']} instead of {f['bloc.F.p1']} and $P(S >= 176)$ "
        f"{f['sens.S.p']} instead of {f['bloc.S.p1']}.",
        f" Una de las encuestas del periodo la publicó un partido ({f['party_released']}); "
        f"sin ella, $P(F >= 176)$ es {f['sens.F.p']} en vez de {f['bloc.F.p1']}, y "
        f"$P(S >= 176)$, {f['sens.S.p']} en vez de {f['bloc.S.p1']}.")
    pg.bullets([
        L(f"Polls: each firm's latest poll with fieldwork ending {nb(f['window'])}, "
          f"{f['firms']} firms; the median of each list. No firm is excluded.",
          "Encuestas: de cada empresa, la última con el trabajo de campo acabado "
          f"{f['window_between']}; son {f['firms']} empresas, y tomo la mediana de cada "
          "lista. No se excluye ninguna.") + party,
        L(f"National error: each share moves on the logit scale with "
          f"$sigma = {f['sigma_nat']}$, the size of the same median's errors {f['lead']} days "
          f"out in 2015–2023 ({f['n_poll_errors']} cases). Errors are centred on zero.",
          "Error nacional: el porcentaje de cada lista se mueve en escala logit con "
          f"$sigma = {mnum(f['sigma_nat'])}$, el tamaño de los errores de la misma mediana a "
          f"{f['lead']} días de las elecciones de 2015–2023 ({f['n_poll_errors']} casos). Los "
          "errores están centrados en cero."),
        L("Constituencies: proportional swing from 2023 (the 2024 European vote for SALF and "
          "to split Sumar's vote), with regional and provincial deviations "
          f"($sigma = {f['tau_ccaa']}$ and {f['tau_prov']}) estimated from past swings; "
          "turnout varies too.",
          "Circunscripciones: el cambio desde 2023 se aplica en proporción (con las europeas "
          "de 2024 para SALF y para repartir el voto de Sumar), con desviaciones autonómicas y "
          f"provinciales ($sigma = {mnum(f['tau_ccaa'])}$ y {f['tau_prov']}) estimadas con "
          "cambios pasados; la participación también varía."),
        L("Seats: D'Hondt with the 3% threshold, and for each list $Delta$, the extra votes it "
          "needs for one more seat.",
          "Escaños: D'Hondt con el umbral del 3 %, y para cada lista $Delta$, los votos que le "
          "faltan para un escaño más.")])
    pg.p(L("The chance that one vote is decisive is the density of $Delta$ at zero:",
           "La probabilidad de que un voto sea decisivo es la densidad de $Delta$ en cero:"))
    pg.eq("p approx N_h / (n h)", "p ≈ N_h / (n h) (2)")
    pg.p(L(f"where $N_h$ counts the $n$ = {f['n']} runs with $0 < Delta <= h$, and $h$ is 2% "
           "of the constituency's votes per seat. With $h$ from 1% to 5% the national answers "
           f"move by {f['seat.bw_spread']} (seat) and {f['majority_any.bw_spread']} (majority). "
           "For a majority, only the runs where that seat moves a bloc across 176 count.",
           f"donde $N_h$ cuenta las simulaciones, de $n$ = {f['n']}, con $0 < Delta <= h$, y "
           "$h$ es el 2 % de los votos por escaño de la circunscripción. Con $h$ entre el 1 % y "
           f"el 5 %, los resultados nacionales se mueven un {f['seat.bw_spread']} (escaño) y un "
           f"{f['majority_any.bw_spread']} (mayoría). Para la mayoría solo cuentan las "
           "simulaciones en que ese escaño cambia si un bloque llega a 176."))
    return pg


def page_backtest(s: dict, f: dict, L: Lang, out: Path, png: Path | None) -> Page:
    pg = Page(L)
    pg.h(L("Does it work? Backtests", "¿Funciona? Contraste con elecciones pasadas"))
    pg.p(L("I ran the same code seven days before the elections of November 2019 and July "
           "2023, calibrated only on earlier elections. The rule for widening the errors was "
           "committed before the first run: widen if fewer than 75% of the actual seat counts "
           "fall in the 80% intervals, or fewer than 90% in the 95% ones. Result: "
           f"{f['bt.in80']} and {f['bt.in95']}, so no widening.",
           "Ejecuté el mismo código siete días antes de las generales de noviembre de 2019 y "
           "de julio de 2023, calibrado solo con las anteriores. La regla para ensanchar los "
           "errores se fijó antes de empezar: si menos del 75 % de las listas queda dentro de "
           "su horquilla del 80 %, o menos del 90 % dentro de la del 95 %. "
           f"Resultado: {f['bt.in80']} y {f['bt.in95']}; no se ensanchan."))
    labels = fig_backtests(s, f, L, out / "fig-backtests.svg",
                           png and png / "fig-backtests.png")
    pg.figure("fig-backtests.svg", 2, L(
        "Simulated 80% (thick) and 95% (thin) intervals and the actual seats (diamonds, filled "
        "when outside the 80% interval).",
        "Horquillas simuladas del 80 % (trazo grueso) y del 95 % (fino) y escaños reales "
        "(rombos, rellenos si quedan fuera de la horquilla del 80 %)."), labels)
    pg.table("(auto, auto, auto, auto)", "(left, center, center, center)",
             [L("Election, bloc", "Elección, bloque"), L("Forecast\nP(≥ 176)", "P(≥ 176)"),
              L("Actual\nseats", "Escaños reales"),
              L("Percentile of\nthe actual", "Percentil del real")],
             [["2023, F", f["bt.2023.F.p"], f["bt.2023.F.actual"], f["bt.2023.F.pctile"]],
              ["2023, S", f["bt.2023.S.p"], f["bt.2023.S.actual"], f["bt.2023.S.pctile"]],
              [L("Nov 2019, investiture bloc", "Noviembre de 2019, S"),
               f["bt.2019N.S.p"], f["bt.2019N.S.actual"], f["bt.2019N.S.pctile"]]],
             caption=L("Where the actual bloc total fell among the simulated ones. 2019 bloc: "
                       "PSOE, Unidas Podemos, PNV, Más País, BNG.",
                       "P(≥ 176) prevista y dónde quedó el total real del bloque entre los "
                       "simulados. S en 2019: PSOE, Unidas Podemos, PNV, Más País y BNG."), n=1)
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
           f"{f['bt_lead.in95']}, "
           f"{verdict}."))
    return pg


def page_seats(s: dict, f: dict, L: Lang, out: Path, png: Path | None) -> Page:
    pg = Page(L)
    pg.h(L("The 2026 parliament", "El Congreso de 2026"))
    labels = fig_seats(s, f, L, out / "fig-seats.svg", png and png / "fig-seats.png")
    pg.figure("fig-seats.svg", 3, L(
        f"Seats per list in {f['n']} simulated elections: mean (circle), 80% (thick) and 95% "
        "(thin) intervals.",
        f"Escaños por lista en {f['n']} elecciones simuladas: media (círculo) y horquillas "
        "del 80 % (trazo grueso) y del 95 % (fino)."), labels)
    rows = []
    for b, name in (("F", "F"), ("S", "S"), ("S_no_JUNTS", L("S without Junts", "S sin Junts"))):
        rows.append([name, f[f"bloc.{b}.mean"], f[f"bloc.{b}.i80"], f[f"bloc.{b}.p"]])
    pg.table("(auto, auto, auto, auto)", "(left, center, center, center)",
             [L("Bloc", "Bloque"), L("Mean\nseats", "Escaños\n(media)"),
              L("80%\ninterval", "Horquilla\ndel 80 %"), "P(≥ 176)"], rows,
             caption=L("The two 2023 investiture blocs.",
                       "Los dos bloques de las investiduras de 2023."), n=2)
    return pg


def page_vote(s: dict, f: dict, L: Lang, out: Path, png: Path | None) -> Page:
    pg = Page(L)
    pg.h(L("What one vote is worth", "Cuánto vale un voto"))
    pg.p(L(f"For the average voter, one more vote changes a seat with probability 1 in "
           f"{f['seat.one_in']}, and changes whether F or S reaches 176 with probability 1 in "
           f"{f['majority_any.one_in']} (F alone 1 in {f['majority_F.one_in']}, S alone 1 in "
           f"{f['majority_S.one_in']}).",
           "Para el votante medio, un voto más cambia un escaño con una probabilidad de 1 "
           f"entre {f['seat.one_in']}, y decide si F o S llega a 176 con una de 1 entre "
           f"{f['majority_any.one_in']} (solo F, 1 entre {f['majority_F.one_in']}; solo S, 1 "
           f"entre {f['majority_S.one_in']})."))
    labels = fig_constituencies(s, f, L, out / "fig-constituencies.svg",
                                png and png / "fig-constituencies.png")
    pg.figure("fig-constituencies.svg", 4, L(
        "The average voter of each of the 52 constituencies.",
        "El votante medio de cada una de las 52 circunscripciones."), labels)
    top = f["seat.top1"]
    pg.p(L(f"Small constituencies weigh more: {f['eps.min']} electors per seat in "
           f"{f['eps.min.name']}, {f['eps.max']} in {f['eps.max.name']}. "
           f"{top}, {race(L, f[f'prov.{top}.seats'])}, is the most decisive "
           f"(1 in {f['seat.top1.one_in']} for its seat, 1 in {f[f'prov.{top}.majority']} for "
           f"the majority); for the majority, {f['majority_any.bottom1']} is the least, at 1 in "
           f"{f['majority_any.bottom1.one_in']}.",
           f"Las circunscripciones pequeñas pesan más: {f['eps.min']} electores por escaño en "
           f"{f['eps.min.name']} y {f['eps.max']} en {f['eps.max.name']}. "
           f"{top}, {race(L, f[f'prov.{top}.seats'])}, es la más decisiva "
           f"(1 entre {f['seat.top1.one_in']} para su escaño y 1 entre "
           f"{f[f'prov.{top}.majority']} para la mayoría); para la mayoría, la que menos es "
           f"{f['majority_any.bottom1']}, con 1 entre {f['majority_any.bottom1.one_in']}."))
    return pg


def page_power(s: dict, f: dict, L: Lang, out: Path, png: Path | None) -> Page:
    pg = Page(L)
    pg.h(L("Who holds the power", "Quién tiene el poder"))
    pg.p(L("Seats are not power. The Shapley–Shubik index is the share of the orders in which "
           "lists could join a coalition where a list's seats carry it past 176. It assumes "
           "any coalition can form: it measures arithmetic leverage, not who will govern.",
           "Tener escaños no es lo mismo que tener poder. El índice de Shapley–Shubik es la "
           "fracción de los órdenes posibles de formar una coalición en los que los escaños de "
           "una lista son los que la llevan a 176. Supone que cualquier coalición puede "
           "formarse: mide peso aritmético, no quién va a gobernar."))
    rows = []
    for p23, p26 in (("PP", "PP"), ("PSOE", "PSOE"), ("VOX", "VOX"), ("SUMAR", "FA"),
                     ("ERC", "ERC"), ("JUNTS", "JUNTS"), ("BILDU", "BILDU"), ("PNV", "PNV")):
        name = DISPLAY[p23] + (f" / {DISPLAY[p26]}" if p26 != p23 else "")
        rows.append([name, f[f"pw23.{p23}.seats"], f[f"pw23.{p23}.ss"], f[f"pw.{p26}.seats"],
                     f[f"pw.{p26}.ss"]])
    pg.table("(auto, auto, auto, auto, auto)", "(left, center, center, center, center)",
             [L("List", "Lista"), L("Seats\n2023", "Escaños\n2023"),
              L("Power\n2023", "Poder\n2023"), L("Seats\n2026 runs", "Escaños\n2026 (sim.)"),
              L("Power\n2026 runs", "Poder\n2026 (sim.)")],
             rows, caption=L("Seat share and Shapley–Shubik power of the lists with 5 or more "
                             "seats in 2023 (Banzhaf agrees closely; README).",
                             "Porcentaje de escaños y poder de Shapley–Shubik de las listas con "
                             "5 escaños o más en 2023 (el índice de Banzhaf da casi lo mismo; "
                             "ver el README)."), n=3)
    players = L("The players", "Los jugadores")
    pg.raw(f"#heading(level: 2, numbering: none)[{T(players)}]", players)
    pg.bullets([
        L("Voters: the outcome ($B$) and the act itself ($D$).",
          "Votantes: el resultado ($B$) y el propio acto de votar ($D$)."),
        L("Parties: votes, office and policy (Strøm, 1990); their leverage is the table above.",
          "Partidos: votos, cargos y políticas (Strøm, 1990); su peso es el de la tabla."),
        L("Pollsters and media: they shape what each player expects the others to do; "
          "LOREG art. 69.7 bans publishing polls in the five days before the vote.",
          "Encuestadoras y medios: forman lo que cada jugador espera que hagan los demás; el "
          "art. 69.7 de la LOREG prohíbe publicar encuestas los cinco días anteriores a la "
          "votación."),
        L("Outside constraints, such as EU fiscal rules, narrow what any majority can do.",
          "Límites externos, como las reglas fiscales de la UE, acotan lo que puede hacer "
          "cualquier mayoría.")])
    return pg


def page_why(s: dict, f: dict, L: Lang, out: Path, png: Path | None) -> Page:
    pg = Page(L)
    pg.h(L("Why vote at all", "¿Por qué votar?"))
    pg.p(L("With three or more options, no ranking rule meets all of Arrow's (1951) "
           "conditions, and every non-dictatorial rule can reward voting against one's true "
           "ranking (Gibbard, 1973; Satterthwaite, 1975). Spain's rule is given; is one vote "
           "worth its cost?",
           "Con tres opciones o más, ninguna regla de ordenación cumple todas las condiciones "
           "de Arrow (1951), y toda regla no dictatorial puede premiar votar en contra de las "
           "propias preferencias (Gibbard, 1973; Satterthwaite, 1975). La regla española es la "
           "que es; ¿compensa un voto lo que cuesta?"))
    pg.p(L(f"At {f['minutes']} minutes and {f['value_of_time']}, $C$ = {f['cost']}. With $p$ "
           f"= 1 in {f['majority_any.one_in']}, a selfish voter breaks even only if the "
           f"majority is worth {f['th.majority.B']} to them (Downs, 1957). If $B$ counts "
           "everyone (Edlin, Gelman and Kaplan, 2007):",
           f"Con {f['minutes']} minutos a {f['value_of_time']}, $C$ = {f['cost']}. Con $p$ = 1 "
           f"entre {f['majority_any.one_in']}, a un votante egoísta solo le sale a cuenta si "
           f"para él la mayoría vale {f['th.majority.B']} (Downs, 1957). Si $B$ cuenta a todos "
           "(Edlin, Gelman y Kaplan, 2007):"))
    pg.eq("B = N b alpha", "B = N b α (3)")
    pg.p(L(f"with $N$ = {f['population']} residents, $b$ the gain per person, $alpha$ the "
           f"weight you give a stranger. Here $p N$ = {f['th.majority.pN']}: with $b$ = 100 €, "
           f"voting pays once $alpha$ passes {f['th.majority.alpha100']}, about 1 in "
           f"{f['th.majority.inv_alpha100']}.",
           f"con $N$ = {f['population']} de residentes, $b$ el beneficio por persona y $alpha$ "
           f"el peso que das a un desconocido. Aquí $p N$ = {f['th.majority.pN']}: con $b$ = "
           f"100 €, votar compensa cuando $alpha$ pasa del {f['th.majority.alpha100']}, más o "
           f"menos 1 entre {f['th.majority.inv_alpha100']}."))
    labels = fig_break_even(s, f, L, out / "fig-break-even.svg",
                            png and png / "fig-break-even.png")
    pg.figure("fig-break-even.svg", 5, L(
        f"Above each line, $p N b alpha$ exceeds the {f['cost']} cost.",
        f"Por encima de cada línea, $p N b alpha$ supera el coste de {f['cost']}."), labels)
    return pg


def page_limits(s: dict, f: dict, L: Lang, out: Path, png: Path | None) -> Page:
    pg = Page(L)
    pg.h(L("Others' votes, limits, takeaways", "Movilizar, límites y conclusiones"))
    pg.p(L("Persuading people barely moves votes in general elections (Kalla and Broockman, "
           "2018); getting them out does, in US experiments (Gerber, Green and Larimer, 2008). "
           f"At an assumed {f['vph_lo']} to {f['vph_hi']} extra voters per hour, an hour beats "
           f"{f['value_of_time']} only if the majority is worth {f['th.majority.infl1.0']} to "
           f"{f['th.majority.infl0.1']} to you, or on the social reckoning of (3).",
           "Convencer apenas mueve votos en unas generales (Kalla y Broockman, 2018); movilizar "
           f"sí, en experimentos en {USA} (Gerber, Green y Larimer, 2008). Suponiendo de "
           f"{f['vph_lo']} a {f['vph_hi']} votantes más por hora, una hora movilizando vale más "
           f"que {f['value_of_time']} solo si la mayoría vale para ti entre "
           f"{f['th.majority.infl1.0']} y {f['th.majority.infl0.1']}, o con la cuenta social "
           "de (3)."))
    for word, text in (
            (L("Limits.", "Límites."), L(
                f"Polls {f['lead']} days out. Proportional swing; SALF and Adelante Andalucía "
                "rest on the 2024 European vote or a flat share. Local lists can surprise. "
                "Blocs fixed by 2023 votes.",
                f"Encuestas a {f['lead']} días. Cambio proporcional; SALF y Adelante Andalucía "
                "se apoyan en las europeas de 2024 o en un porcentaje fijo. Las listas locales "
                "pueden sorprender. Bloques fijados por las votaciones de 2023.")),
            (L("Takeaways.", "Conclusiones."), L(
                "A seat is a far likelier prize than the majority. Between constituencies the "
                "odds of deciding the majority differ by a factor of up to "
                f"{f['majority_any.spread']}. Selfishly, voting rarely pays; counting others, "
                "it can.",
                "Un escaño es un premio mucho más probable que la mayoría. Entre "
                "circunscripciones, la probabilidad de decidir la mayoría varía hasta "
                f"{f['majority_any.spread']} veces. Por interés propio, votar rara vez "
                "compensa; contando a los demás, puede compensar."))):
        pg.raw(f"#emph[{T(word)}] " + T(text), f"{word} " + P(text))
    pg.raw(f"#align(center, strong[{T(REPO)}])", REPO)
    refs = [f"[{T(lead)} #emph[{T(journal)}] {T(tail)}]" for lead, journal, tail in REFERENCES]
    pg.raw("#block(above: 0.6em, {\n  set text(8.6pt)\n  set par(justify: false, "
           "hanging-indent: 1.0em, leading: 0.3em, spacing: 0.32em)\n  "
           + "\n  parbreak()\n  ".join(refs) + "\n})")
    pg.refs = [f"{lead} {journal} {tail}" for lead, journal, tail in REFERENCES]
    return pg


FIGURES = [("fig-odds", fig_odds), ("fig-backtests", fig_backtests), ("fig-seats", fig_seats),
           ("fig-constituencies", fig_constituencies), ("fig-break-even", fig_break_even)]


def make_figures(results_dir: Path, figures_dir: Path, lang: str = "en") -> None:
    """The five figures alone, as PNG and SVG, for the README."""
    style.paper_style()
    summary = style.load_summary(results_dir)
    L, f = Lang(lang), fx.build(summary, lang)
    out = Path(figures_dir)
    out.mkdir(parents=True, exist_ok=True)
    for name, draw in FIGURES:
        draw(summary, f, L, out / f"{name}.svg", out / f"{name}.png")
        print(f"-> {out / name}.png")


PAGES = [page_title, page_question, page_model, page_backtest, page_seats, page_vote,
         page_power, page_why, page_limits]


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
    m = L.meta
    source = (PREAMBLE.replace("@TITLE", m["title"]).replace("@AUTHOR", AUTHOR)
              .replace("@SHORT", T(m["short"])).replace("@LANG", m["typst"])
              .replace("@NAMES", r"\b(?:" + "|".join(NAMES) + r")\b"))
    source += "\n" + "\n\n#pagebreak()\n\n".join(pg.markup() for pg in pages) + "\n"
    typ = out / "carousel.typ"
    typ.write_text(source)
    common = {"root": str(out), "font_paths": [str(style.FONTS)], "ignore_system_fonts": True}
    pdf_path = out / "carousel.pdf"
    typst.compile(str(typ), output=str(pdf_path), **common)
    typst.compile(str(typ), output=str(out / "slide-{p}.png"), format="png", ppi=180, **common)
    pngs = sorted(out.glob("slide-*.png"), key=lambda p: int(re.search(r"\d+", p.name)[0]))
    for i, png in enumerate(pngs, start=1):
        png.rename(out / f"slide-{i:02d}.png")
    if len(pngs) != len(PAGES):
        print(f"  warning: {len(pngs)} pages for {len(PAGES)} slides: something overflows")
    text = [f"## {m['slide']} {i}\n\n" + "\n\n".join(t for t in pg.txt if t.strip())
            for i, pg in enumerate(pages, start=1)]
    (out / "slides.txt").write_text("\n\n".join(text) + f"\n\n## {m['references']}\n\n" +
                                    "\n".join(pages[-1].refs) + "\n")
    print(f"-> {pdf_path} ({len(pngs)} pages), {out / 'slides.txt'}")
