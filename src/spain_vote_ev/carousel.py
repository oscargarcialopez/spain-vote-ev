"""The LinkedIn carousel: nine 4:5 pages (6 x 7.5 in, previews at 1080 x 1350 px) set like a
paper. STIX Two type (vendored in fonts/), numbered sections and equations, captioned figures,
ruled tables and the references; black and greys and one brown accent that is no party's
colour. Typst sets the pages and matplotlib draws the figures as SVG (PNG copies go to
figures/ for the README).

Every number comes from results/summary.json through facts.build(). carousel/slides.txt holds
the pages as plain text: a text alternative, and the input for `voteev check`.
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

TITLE = "What is one vote worth?"
SUBTITLE = "Spain's general election of 29 November 2026"
SHORT = "What is one vote worth? Spain, 29 November 2026"
AUTHOR = "Óscar García López"
DATE = "November 2026"
REPO = "github.com/oscargarcialopez/spain-vote-ev"
TEXT_W = 4.9  # inches: a 6 in page with 0.55 in margins

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
#set text(font: "STIX Two Text", size: 13pt, lang: "en", region: "gb")
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

MATH_DOLLAR = re.compile(r"(?<!\\)\$")


def _esc(text: str) -> str:
    """Plain text as Typst markup: escape what would start markup; a literal $ is \\$."""
    text = text.replace("\\$", "\x00")
    text = re.sub(r"([\\#*_@<>\[\]`~/=+-])", r"\\\1", text)
    return text.replace("\x00", "\\$")


def T(src: str) -> str:
    """Typst markup from text with $inline math$ (Typst math syntax)."""
    parts = MATH_DOLLAR.split(src)
    return "".join(_esc(p) if i % 2 == 0 else f"#box[${p}$]" for i, p in enumerate(parts))


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


def head(h: str) -> str:
    return "[" + " \\ ".join(T(part) for part in h.split("\n")) + "]"


def cell(x: str) -> str:
    return "[" + T(x) + "]"


class Page:
    """One page: Typst markup blocks and the same content as plain text, in reading order."""

    def __init__(self):
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
        self.raw(f'#align(center, image("{name}"))\n#cap("Figure", {n})[{T(caption)}]',
                 [f"Figure {n}. {P(caption)}"] + labels)

    def table(self, cols: str, aligns: str, header: list[str], rows: list[list[str]],
              caption: str | None = None, n: int | None = None) -> None:
        cells = ", ".join(cell(x) for r in rows for x in r)
        typ = f"#ruled({cols}, {aligns}, ({', '.join(head(h) for h in header)},), {cells})"
        txt = [" | ".join(h.replace("\n", " ") for h in header)]
        txt += [" | ".join(P(x) for x in r) for r in rows]
        if caption:
            typ = f'#cap("Table", {n}, above: 0.9em)[{T(caption)}]\n' + typ
            txt = [f"Table {n}. {P(caption)}"] + txt
        self.raw(typ, txt)

    def markup(self) -> str:
        return "\n\n".join(self.typ)


# --- figures --------------------------------------------------------------------------------


def texts(fig) -> list[str]:
    """The words on a figure that are not tick numbers."""
    out = []
    for ax in fig.axes:
        out += [t.get_text() for t in ax.texts]
        out += [ax.get_xlabel(), ax.get_ylabel()]
        for t in [*ax.get_yticklabels(), *ax.get_xticklabels()]:
            if re.search("[A-Za-z]", t.get_text()):
                out.append(t.get_text())
        if ax.get_legend():
            out += [t.get_text() for t in ax.get_legend().get_texts()]
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


ODDS_TICKS = [(1e3, "1,000"), (1e4, "10,000"), (1e5, "100,000"), (1e6, "1 million"),
              (1e7, "10 million"), (1e8, "100 million")]


def fig_odds(s: dict, f: dict, svg: Path, png: Path | None) -> list[str]:
    nat = s["vote"]["national"]
    rows = [("one vote changes a seat", nat["seat"]["one_in"], f["seat.one_in"], True),
            ("one vote changes whether a bloc has 176 seats", nat["majority_any"]["one_in"],
             f["majority_any.one_in"], True),
            ("picking all six numbers of 49", fx.LOTTERY, f["lottery"], False),
            ("one vote decides the 2008 US presidency", s["context"]["gse_2012_one_in"],
             f["gse"], False)]
    fig, ax = plt.subplots(figsize=(TEXT_W, 2.05))
    for k, (label, val, txt, ours) in enumerate(rows):
        y = -k
        ax.barh(y, val - 300, left=300, height=0.42, color=INK if ours else "white",
                edgecolor=INK, hatch=None if ours else "////", lw=0.6)
        ax.text(330, y + 0.36, label, fontsize=10.5, va="bottom")
        ax.text(val * 1.35, y, f"1 in {txt}", fontsize=10.5, va="center")
    ax.set_xscale("log")
    ax.set_xlim(300, 2e9)
    ax.set_ylim(-len(rows) + 0.45, 0.95)
    ax.set_yticks([])
    ax.set_xticks([t for t, _ in ODDS_TICKS], [lab for _, lab in ODDS_TICKS], fontsize=9.5)
    ax.minorticks_off()
    ax.set_xlabel("odds, 1 in N (log scale)", fontsize=11)
    return save(fig, svg, png)


def fig_seats(s: dict, f: dict, svg: Path, png: Path | None) -> list[str]:
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
    ax.set_xlabel("seats", fontsize=11)
    ax.tick_params(axis="y", length=0)
    return save(fig, svg, png)


def fig_constituencies(s: dict, f: dict, svg: Path, png: Path | None) -> list[str]:
    prov = s["vote"]["provinces"]
    seats = np.array([r["seats"] for r in prov], float)
    jitter = 1 + 0.035 * (np.arange(len(prov)) % 3 - 1)
    fig, ax = plt.subplots(figsize=(TEXT_W, 2.7))
    ax.plot(seats * jitter, [r["one_in_seat"] for r in prov], "o", ms=3.6, mfc=INK, mec=INK,
            mew=0.5, label="changes a seat")
    ax.plot(seats * jitter, [r["one_in_majority_any"] for r in prov], "o", ms=3.8,
            mfc="white", mec=ACCENT, mew=0.9, label="changes whether a bloc has 176")
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlim(0.8, 50)
    ax.set_ylim(4e3, 2e8)
    ax.set_xticks([1, 2, 5, 10, 20, 37], ["1", "2", "5", "10", "20", "37"])
    ax.minorticks_off()
    ax.set_yticks([1e4, 1e5, 1e6, 1e7, 1e8],
                  ["10,000", "100,000", "1 million", "10 million", "100 million"], fontsize=9.5)
    ax.set_xlabel("seats in the constituency (log scale)", fontsize=11)
    ax.set_ylabel("odds, 1 in N", fontsize=11)
    for key in ("seat.top1", "seat.bottom1", "majority_any.bottom1", "majority_any.top2"):
        r = next(x for x in prov if x["name"] == f[key])
        ev = "seat" if key.startswith("seat") else "majority_any"
        ax.annotate(r["name"], (r["seats"], r[f"one_in_{ev}"]), xytext=(5, 2),
                    textcoords="offset points", fontsize=9.5, color=GREY)
    ax.legend(loc="lower left", fontsize=9.5, handletextpad=0.3, borderpad=0.4)
    return save(fig, svg, png)


def fig_break_even(s: dict, f: dict, svg: Path, png: Path | None) -> list[str]:
    th = s["theory"]
    b = theory.B_GRID
    fig, ax = plt.subplots(figsize=(TEXT_W, 2.55))
    a_maj = theory.break_even_alpha(th["majority"]["p"], th["population"], b)
    a_seat = theory.break_even_alpha(th["seat"]["p"], th["population"], b)
    ax.fill_between(b, a_maj, 1, color=FILL, lw=0)
    ax.plot(b, a_maj, color=INK, lw=1.1, label="majority: $p$ = 1 in " +
            f["majority_any.one_in"])
    ax.plot(b, a_seat, color=GREY, lw=1.0, ls="--", label="a seat: $p$ = 1 in " +
            f["seat.one_in"])
    ax.plot([100], [th["majority"]["alpha_for_b_100"]], "o", ms=4.5, mfc="white", mec=ACCENT,
            mew=1.0)
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlim(1, 1e5)
    ax.set_ylim(1e-6, 1)
    ax.set_xticks([1, 10, 100, 1e3, 1e4, 1e5], ["1", "10", "100", "1,000", "10,000",
                                                 "100,000"])
    ax.set_yticks([1e-6, 1e-4, 1e-2, 1], ["0.0001%", "0.01%", "1%", "100%"])
    ax.minorticks_off()
    ax.text(2.0, 0.08, "voting pays", fontsize=11)
    ax.set_xlabel("$b$, gain per person from the outcome (€)", fontsize=11)
    ax.set_ylabel("$\\alpha$, weight on others", fontsize=11)
    ax.legend(loc="lower left", fontsize=9.5, handlelength=1.6)
    return save(fig, svg, png)


# --- the pages ------------------------------------------------------------------------------


def page_title(s: dict, f: dict, out: Path, png: Path | None) -> Page:
    pg = Page()
    pg.raw("#align(center)[\n  #v(2pt)\n"
           f"  #text(21pt, weight: \"bold\", hyphenate: false)[{T(TITLE)}]\n  #v(2pt)\n"
           f"  #text(14.5pt, style: \"italic\")[{T(SUBTITLE)}]\n  #v(8pt)\n"
           f"  #text(13pt)[{T(AUTHOR)}]\n  #v(-2pt)\n  #text(11.5pt)[{T(DATE)}]\n]",
           [TITLE, SUBTITLE, AUTHOR, DATE])
    abstract = (
        f"I simulate Spain's election {f['n']} times from the polls to {f['cutoff']}, "
        "constituency by constituency, with errors measured on the same poll summary in "
        "past elections. For the average voter, one more vote changes a seat with probability "
        f"1 in {f['seat.one_in']}, and changes whether either 2023 investiture bloc reaches 176 "
        f"seats with probability 1 in {f['majority_any.one_in']}: about {f['ratio_gse']} times "
        "likelier than deciding the 2008 US presidency, and close to the odds of picking all "
        "six numbers of 49. The numbers treat every list alike and advise no one.")
    pg.raw("#v(4pt)\n#align(center, text(12.5pt, weight: \"bold\")[Abstract])\n#v(-3pt)\n"
           f"#pad(x: 1.0em)[#set text(12pt)\n#set par(leading: 0.45em)\n{T(abstract)}]",
           ["Abstract", P(abstract)])
    labels = fig_odds(s, f, out / "fig-1.svg", png and png / "fig-1-odds.png")
    pg.raw("#v(2pt)")
    pg.figure("fig-1.svg", 1, "How likely one vote is to decide. Black: this model, average "
              "Spanish voter. Hatched: references (Gelman, Silver and Edlin, 2012).", labels)
    note = "Code, data and method: linked in the first comment."
    pg.raw("#v(1fr)\n#block(width: 100%, {\n  line(length: 30%, stroke: 0.4pt)\n  v(-4pt)\n"
           f"  text(10.5pt)[{T(note)}]\n}})", P(note))
    return pg


def page_question(s: dict, f: dict, out: Path, png: Path | None) -> Page:
    pg = Page()
    pg.h("The question")
    pg.p("A vote matters when it changes something. Spain elects 350 deputies in 52 "
         "constituencies by D'Hondt, with a 3% threshold in each; Ceuta and Melilla elect one "
         "each. One more vote can move a seat from one list to another, or move the seat that "
         "decides a majority of 176.")
    pg.p("For the majority I use the coalitions of the two 2023 investiture votes, so no "
         "party is placed by anyone's judgement:")
    fe, sa = "inv.feijoo", "inv.sanchez"
    pg.table("(auto, auto, 1fr)", "(left, left, left)", ["Bloc", "Vote", "Yes votes"], [
        ["F", f"Feijóo, 27 Sep 2023: {f[fe + '.yes']}",
         f"PP {f[fe + '.PP']}, Vox {f[fe + '.VOX']}, UPN {f[fe + '.UPN']}, CC {f[fe + '.CC']}"],
        ["S", f"Sánchez, 16 Nov 2023: {f[sa + '.yes']}",
         f"PSOE {f[sa + '.PSOE']}, Sumar {f[sa + '.SUMAR']}, ERC {f[sa + '.ERC']}, "
         f"Junts {f[sa + '.JUNTS']}, EH Bildu {f[sa + '.BILDU']}, PNV {f[sa + '.PNV']}, "
         f"BNG {f[sa + '.BNG']}, CC {f[sa + '.CC']}"]])
    pg.p("Frente Amplio and Podemos, both in Sumar's group in 2023, count in S; lists with no "
         "seat in 2023 count in neither; Coalición Canaria voted yes twice, so it is in both. "
         "I also report S without Junts.")
    pg.p("Whether voting pays is the calculus of voting (Riker and Ordeshook, 1968):")
    pg.eq("R = p B - C + D", "R = pB − C + D (1)")
    pg.p("where $p$ is the chance of being decisive, $B$ what the outcome is worth to you, "
         "$C$ the cost of voting and $D$ what voting is worth in itself. This study estimates "
         "$p$.")
    return pg


def page_model(s: dict, f: dict, out: Path, png: Path | None) -> Page:
    pg = Page()
    pg.h("The model")
    party = (f" One poll in the window was released by a party ({f['party_released']}); "
             f"without it, $P(F >= 176)$ is {f['sens.F.p']} instead of {f['bloc.F.p1']} and "
             f"$P(S >= 176)$ {f['sens.S.p']} instead of {f['bloc.S.p1']}."
             if f["party_released"] != "none" else "")
    pg.bullets([
        f"Polls: each firm's latest poll with fieldwork ending {f['window']}, "
        f"{f['firms']} firms; the median of each list. No firm is excluded."
        + party,
        f"National error: each share moves on the logit scale with $sigma$ = {f['sigma_nat']}, "
        f"the size of the same median's errors {f['lead']} days out in 2015–2023 "
        f"({f['n_poll_errors']} cases). Errors are centred on zero.",
        "Constituencies: proportional swing from 2023 (the 2024 European vote for SALF and to "
        f"split Sumar's vote), with regional and provincial deviations ($sigma$ = "
        f"{f['tau_ccaa']} and {f['tau_prov']}) estimated from past swings; turnout varies too.",
        "Seats: D'Hondt with the 3% threshold, and for each list $Delta$, the extra votes it "
        "needs for one more seat."])
    pg.p("The chance that one vote is decisive is the density of $Delta$ at zero:")
    pg.eq("p approx N_h / (n h)", "p ≈ N_h / (n h) (2)")
    pg.p(f"where $N_h$ counts the $n$ = {f['n']} runs with $0 < Delta <= h$, and $h$ is 2% of "
         "the constituency's votes per seat. With $h$ from 1% to 5% the national answers move "
         f"by {f['seat.bw_spread']} (seat) and {f['majority_any.bw_spread']} (majority). For a "
         "majority, only the runs where that seat moves a bloc across 176 count.")
    return pg


def page_backtest(s: dict, f: dict, out: Path, png: Path | None) -> Page:
    pg = Page()
    pg.h("Does it work? Backtests")
    pg.p("I ran the same code seven days before the elections of November 2019 and July "
         "2023, calibrated only on earlier elections. The rule for widening the errors was "
         "committed before the first run: widen if fewer than 75% of the actual seat counts "
         "fall in the 80% intervals, or fewer than 90% in the 95% ones.")
    pg.p(f"Result: {f['bt.in80']} lists inside their 80% intervals, {f['bt.in95']} inside the "
         "95% ones, so no widening. The 80% misses: "
         f"{f['bt.2019N.misses80']} in 2019; {f['bt.2023.misses80']} in 2023.")
    pg.table("(auto, auto, auto, auto)", "(left, center, center, center)",
             ["Election, bloc", "Forecast\nP(≥ 176)", "Actual\nseats",
              "Percentile of\nthe actual"],
             [["2023, F", f["bt.2023.F.p"], f["bt.2023.F.actual"], f["bt.2023.F.pctile"]],
              ["2023, S", f["bt.2023.S.p"], f["bt.2023.S.actual"], f["bt.2023.S.pctile"]],
              ["Nov 2019, investiture bloc", f["bt.2019N.S.p"], f["bt.2019N.S.actual"],
               f["bt.2019N.S.pctile"]]],
             caption="Where the actual bloc total fell in the simulated distribution. The "
                     "2019 bloc is PSOE, Unidas Podemos, PNV, Más País and BNG.", n=1)
    pg.p(f"Run {f['lead']} days out, as for 2026, coverage is {f['bt_lead.in80']} and "
         f"{f['bt_lead.in95']}: a little short at 95%, so the 2026 intervals may be slightly "
         "narrow.")
    return pg


def page_seats(s: dict, f: dict, out: Path, png: Path | None) -> Page:
    pg = Page()
    pg.h("The 2026 parliament")
    labels = fig_seats(s, f, out / "fig-2.svg", png and png / "fig-2-seats.png")
    pg.figure("fig-2.svg", 2, f"Seats per list in {f['n']} simulated elections: mean (circle), "
              "80% (thick) and 95% (thin) intervals.", labels)
    rows = []
    for b, name in (("F", "F"), ("S", "S"), ("S_no_JUNTS", "S without Junts")):
        rows.append([name, f[f"bloc.{b}.mean"], f[f"bloc.{b}.i80"], f[f"bloc.{b}.p"]])
    pg.table("(auto, auto, auto, auto)", "(left, center, center, center)",
             ["Bloc", "Mean\nseats", "80%\ninterval", "P(≥ 176)"], rows,
             caption="The two 2023 investiture blocs.", n=2)
    return pg


def page_vote(s: dict, f: dict, out: Path, png: Path | None) -> Page:
    pg = Page()
    pg.h("What one vote is worth")
    pg.p(f"For the average voter, one more vote changes a seat with probability 1 in "
         f"{f['seat.one_in']}, and changes whether F or S reaches 176 with probability 1 in "
         f"{f['majority_any.one_in']} (F alone 1 in {f['majority_F.one_in']}, S alone 1 in "
         f"{f['majority_S.one_in']}).")
    labels = fig_constituencies(s, f, out / "fig-3.svg", png and png / "fig-3-constituencies.png")
    pg.figure("fig-3.svg", 3, "The average voter of each of the 52 constituencies.", labels)
    pg.p(f"Small constituencies weigh more: {f['eps.min']} electors per seat in "
         f"{f['eps.min.name']}, {f['eps.max']} in {f['eps.max.name']}. "
         f"{f['seat.top1']}, a one-seat race, is the most decisive (1 in "
         f"{f['seat.top1.one_in']} for its seat, 1 in {f['majority_any.top1.one_in']} for "
         f"the majority); for the majority, {f['majority_any.bottom1']} is the least, at "
         f"1 in {f['majority_any.bottom1.one_in']}.")
    return pg


def page_power(s: dict, f: dict, out: Path, png: Path | None) -> Page:
    pg = Page()
    pg.h("Who holds the power")
    pg.p("Seats are not power. The Shapley–Shubik index is the share of the orders in which "
         "lists could join a coalition where a list's seats carry it past 176. It assumes any "
         "coalition can form: it measures arithmetic leverage, not who will govern.")
    rows = []
    for p23, p26 in (("PP", "PP"), ("PSOE", "PSOE"), ("VOX", "VOX"), ("SUMAR", "FA"),
                     ("ERC", "ERC"), ("JUNTS", "JUNTS"), ("BILDU", "BILDU"), ("PNV", "PNV")):
        name = DISPLAY[p23] + (f" / {DISPLAY[p26]}" if p26 != p23 else "")
        rows.append([name, f[f"pw23.{p23}.seats"], f[f"pw23.{p23}.ss"], f[f"pw.{p26}.seats"],
                     f[f"pw.{p26}.ss"]])
    pg.table("(auto, auto, auto, auto, auto)", "(left, center, center, center, center)",
             ["List", "Seats\n2023", "Power\n2023", "Seats\n2026 runs", "Power\n2026 runs"],
             rows, caption="Seat share and Shapley–Shubik power of the lists with 5 or "
                           "more seats in 2023 (Banzhaf agrees closely; README).", n=3)
    pg.raw("#heading(level: 2, numbering: none)[The players]", "The players")
    pg.bullets([
        "Voters: the outcome ($B$) and the act itself ($D$).",
        "Parties: votes, office and policy (Strøm, 1990); their leverage is the table above.",
        "Pollsters and media: they shape what each player expects the others to do; "
        "LOREG art. 69.7 bans publishing polls in the five days before the vote.",
        "Outside constraints, such as EU fiscal rules, narrow what any majority can do."])
    return pg


def page_why(s: dict, f: dict, out: Path, png: Path | None) -> Page:
    pg = Page()
    pg.h("Why vote at all")
    pg.p("With three or more options, no ranking rule meets all of Arrow's (1951) conditions, "
         "and every non-dictatorial rule can reward voting against one's true ranking "
         "(Gibbard, 1973; Satterthwaite, 1975). Spain's rule is given; is one vote worth its "
         "cost?")
    pg.p(f"At {f['minutes']} minutes and {f['value_of_time']}, $C$ = {f['cost']}. With $p$ = 1 "
         f"in {f['majority_any.one_in']}, a selfish voter breaks even only if the majority is "
         f"worth {f['th.majority.B']} to them (Downs, 1957). If $B$ counts everyone (Edlin, "
         "Gelman and Kaplan, 2007):")
    pg.eq("B = N b alpha", "B = N b α (3)")
    pg.p(f"with $N$ = {f['population']} residents, $b$ the gain per person, $alpha$ the "
         f"weight you give a stranger. Here $p N$ = {f['th.majority.pN']}: with $b$ = 100 €, "
         f"voting pays once $alpha$ passes {f['th.majority.alpha100']}, about 1 in "
         f"{f['th.majority.inv_alpha100']}.")
    labels = fig_break_even(s, f, out / "fig-4.svg", png and png / "fig-4-break-even.png")
    pg.figure("fig-4.svg", 4, "Above each line, $p N b alpha$ exceeds the 5 € cost.", labels)
    return pg


def page_limits(s: dict, f: dict, out: Path, png: Path | None) -> Page:
    pg = Page()
    pg.h("Others' votes, limits, takeaways")
    pg.p("Persuading people barely moves votes in general elections (Kalla and Broockman, "
         "2018); getting them out does, in US experiments (Gerber, Green and Larimer, 2008). "
         f"At an assumed {f['vph_lo']} to {f['vph_hi']} extra voters per hour, an hour beats "
         f"{f['value_of_time']} only if the majority is worth {f['th.majority.infl1.0']} to "
         f"{f['th.majority.infl0.1']} to you, or on the social reckoning of (3).")
    pg.raw("#emph[Limits.] " + T(
        f"Polls {f['lead']} days out. Proportional swing; SALF and Adelante Andalucía rest on "
        "the 2024 European vote or a flat share. Local lists can surprise. Blocs fixed by "
        "2023 votes."), "Limits. " + P(
        f"Polls {f['lead']} days out. Proportional swing; SALF and Adelante Andalucía rest on "
        "the 2024 European vote or a flat share. Local lists can surprise. Blocs fixed by "
        "2023 votes."))
    pg.raw("#emph[Takeaways.] " + T(
        f"A seat is a far likelier prize than the majority. Between constituencies the odds "
        f"of deciding the majority differ up to {f['majority_any.spread']}-fold. Selfishly, "
        "voting rarely pays; counting others, it can."), "Takeaways. " + P(
        f"A seat is a far likelier prize than the majority. Between constituencies the odds "
        f"of deciding the majority differ up to {f['majority_any.spread']}-fold. Selfishly, "
        "voting rarely pays; counting others, it can."))
    pg.raw(f"#align(center, strong[{T(REPO)}])", REPO)
    refs = [f"[{T(lead)} #emph[{T(journal)}] {T(tail)}]" for lead, journal, tail in REFERENCES]
    pg.raw("#block(above: 0.6em, {\n  set text(8.6pt)\n  set par(justify: false, "
           "hanging-indent: 1.0em, leading: 0.3em, spacing: 0.32em)\n  "
           + "\n  parbreak()\n  ".join(refs) + "\n})")
    pg.refs = [f"{lead} {journal} {tail}" for lead, journal, tail in REFERENCES]
    return pg


FIGURES = [("fig-1-odds", fig_odds), ("fig-2-seats", fig_seats),
           ("fig-3-constituencies", fig_constituencies), ("fig-4-break-even", fig_break_even)]


def make_figures(results_dir: Path, figures_dir: Path) -> None:
    """The four figures alone, as PNG and SVG, for the README."""
    style.paper_style()
    summary = style.load_summary(results_dir)
    f = fx.build(summary)
    out = Path(figures_dir)
    out.mkdir(parents=True, exist_ok=True)
    for name, draw in FIGURES:
        draw(summary, f, out / f"{name}.svg", out / f"{name}.png")
        print(f"-> {out / name}.png")


PAGES = [page_title, page_question, page_model, page_backtest, page_seats, page_vote,
         page_power, page_why, page_limits]


def make_carousel(results_dir: Path, carousel_dir: Path, figures_dir: Path | None = None
                  ) -> None:
    logging.getLogger("fontTools").setLevel(logging.ERROR)
    style.paper_style()
    summary = style.load_summary(results_dir)
    f = fx.build(summary)
    out = Path(carousel_dir)
    out.mkdir(parents=True, exist_ok=True)
    if figures_dir is not None:
        Path(figures_dir).mkdir(parents=True, exist_ok=True)
    for old in [*out.glob("slide-*.png"), *out.glob("fig-*.svg")]:
        old.unlink()
    pages = [make(summary, f, out, figures_dir) for make in PAGES]
    source = (PREAMBLE.replace("@TITLE", TITLE).replace("@AUTHOR", AUTHOR)
              .replace("@SHORT", T(SHORT)))
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
    text = [f"## Slide {i}\n\n" + "\n\n".join(t for t in pg.txt if t.strip())
            for i, pg in enumerate(pages, start=1)]
    (out / "slides.txt").write_text("\n\n".join(text) + "\n\n## References\n\n" +
                                    "\n".join(pages[-1].refs) + "\n")
    print(f"-> {pdf_path} ({len(pngs)} pages)")
