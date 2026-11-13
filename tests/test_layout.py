"""The gap check of the carousels (layout.py)."""

import pytest

from spain_vote_ev import layout
from spain_vote_ev.sources import ROOT

SPACE = 0.235 * 13  # STIX Two Text's space at 13 pt, in points


def glyph(text, x0, width=5.0, size=13.0, y=100.0, font="STIXTwoText-Regular"):
    return {"text": text, "x0": x0, "x1": x0 + width, "size": size, "fontname": font,
            "matrix": (1, 0, 0, 1, x0, y)}


def test_gaps_are_measured_in_the_fonts_spaces():
    line = [glyph("a", 0), glyph(" ", 5, SPACE), glyph("b", 5 + 2.5 * SPACE)]
    text, gaps = layout.line_gaps(line)
    assert text == "a b"
    assert gaps == pytest.approx([2.5])


def test_a_justified_line_is_as_loose_as_its_spaces():
    assert layout.stretch([2.4, 2.4, 2.4]) == pytest.approx(2.4)


def test_a_table_cell_boundary_is_not_a_loose_line():
    # "Without the poll released by a | 94.3%": one wide gap among normal spaces
    assert layout.stretch([1.0, 1.0, 1.0, 1.0, 1.0, 16.1]) == pytest.approx(1.0)


def test_a_subscript_belongs_to_its_line():
    chars = [glyph("N", 0, 8), glyph("h", 8, 4, size=9.0, y=97.5), glyph("x", 0, y=80.0)]
    assert [len(line) for line in layout._lines(chars)] == [2, 1]


@pytest.mark.parametrize("pdf", ["carousel/carousel.pdf", "carousel/en/carousel.pdf"])
def test_published_carousels_have_no_wide_gaps(pdf):
    path = ROOT / pdf
    if not path.exists():
        pytest.skip(f"{pdf} not built")
    assert [str(g) for g in layout.wide_gaps(path)] == []


@pytest.mark.parametrize("pdf", ["carousel/carousel.pdf", "carousel/en/carousel.pdf"])
def test_published_carousels_have_one_page_per_slide(pdf):
    from spain_vote_ev.carousel import PAGES
    path = ROOT / pdf
    if not path.exists():
        pytest.skip(f"{pdf} not built")
    assert layout.page_count(path) == len(PAGES)
