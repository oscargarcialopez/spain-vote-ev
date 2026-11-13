"""Justified lines with gaps that are too wide: a check on the carousel PDFs.

Justification stretches the spaces of a line until it fills the measure; a short line with a
long unbreakable word (a number, a formula) can end up with holes. A line is too loose when
its spaces are more than LIMIT times the font's own space (STIX Two Text: 0.235 em upright,
0.225 em italic). Typst stretches every space of a line, no-break ones included, by the same
amount, so a line's stretch is its median gap: a single wide gap among normal ones is the
boundary between two table cells on the same baseline, not justification. Lines are rebuilt
from the glyphs' baselines, so a subscript belongs to its line, and only the running text,
abstract, captions and tables are read (SIZES).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from statistics import median

LIMIT = 2.0
SIZES = (11.0, 12.0, 13.0)  # captions, abstract, running text (points)
SPACES = (" ", " ")


@dataclass(frozen=True)
class Gap:
    page: int
    ratio: float  # the line's stretch: its median interword gap, in the font's spaces
    line: str

    def __str__(self) -> str:
        return f"page {self.page}: gap {self.ratio:.1f}x in “{self.line.strip()}”"


def _space_em(font: str) -> float:
    return 0.225 if "Italic" in font else 0.235


def _lines(chars: list[dict]) -> list[list[dict]]:
    """Glyphs grouped by baseline: a sub- or superscript joins the line it sits on."""
    out: list[list[dict]] = []
    for c in sorted(chars, key=lambda c: -c["matrix"][5]):
        if out and abs(out[-1][0]["matrix"][5] - c["matrix"][5]) < 0.45 * out[-1][0]["size"]:
            out[-1].append(c)
        else:
            out.append([c])
    return out


def line_gaps(line: list[dict]) -> tuple[str, list[float]]:
    """The line's text and each interword gap in units of the preceding font's space."""
    line = sorted(line, key=lambda c: c["x0"])
    text = "".join(c["text"] for c in line)
    gaps, prev, spaced = [], None, False
    for c in line:
        if c["text"] in SPACES:
            spaced = True
            continue
        if prev is not None and spaced:
            gaps.append((c["x0"] - prev["x1"]) / (_space_em(prev["fontname"]) * prev["size"]))
        prev, spaced = c, False
    return text, gaps


def stretch(gaps: list[float]) -> float:
    """How far justification stretched a line's spaces (1 = not at all)."""
    return median(gaps) if gaps else 1.0


def wide_gaps(pdf: Path | str, limit: float = LIMIT) -> list[Gap]:
    """Every checked line whose spaces are stretched beyond `limit` times their width."""
    import pdfplumber
    out = []
    with pdfplumber.open(str(pdf)) as doc:
        for number, page in enumerate(doc.pages, start=1):
            for line in _lines(page.chars):
                body = [c for c in line if c["text"] not in SPACES]
                sizes = [round(c["size"], 1) for c in body]
                if not sizes or max(set(sizes), key=sizes.count) not in SIZES:
                    continue
                text, gaps = line_gaps(line)
                if gaps and stretch(gaps) > limit:
                    out.append(Gap(number, stretch(gaps), text))
    return out


def page_count(pdf: Path | str) -> int:
    import pdfplumber
    with pdfplumber.open(str(pdf)) as doc:
        return len(doc.pages)


def worst(pdf: Path | str, k: int = 10) -> list[Gap]:
    """The k lines with the widest gaps, wide or not: for rewording."""
    return sorted(wide_gaps(pdf, limit=0.0), key=lambda g: -g.ratio)[:k]
