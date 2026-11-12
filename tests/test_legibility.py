"""The type floor (legibility.py): the criterion's numbers, the checkers, and both carousels.

Fails if any glyph of either carousel PDF (pdfplumber, per font style) or any text in their
figures (matplotlib) is below its style's minimum."""

import math

import pytest
import typst
from PIL import Image

from spain_vote_ev import carousel, style
from spain_vote_ev import legibility as lg
from spain_vote_ev.cli import CAROUSELS
from spain_vote_ev.sources import RESULTS, ROOT


def test_the_floor_follows_the_criterion():
    assert lg.x_height("regular") == lg.x_height("bold") == lg.x_height("math") == 0.473
    assert lg.x_height("italic") == 0.467
    assert abs(lg.SCREEN_MM - 65.1) < 0.005
    assert lg.raw_min_pt("regular") == pytest.approx(15.77, abs=0.005)
    assert lg.raw_min_pt("italic") == pytest.approx(15.97, abs=0.005)
    assert lg.MIN_PT == {"regular": 15.8, "italic": 16.0, "bold": 15.8, "bolditalic": 15.8,
                         "math": 15.8}
    assert lg.BODY_PT == 15.8 and lg.ITALIC_PT == 16.0 and lg.PX_PER_PT == 2.5
    for name, size in lg.MIN_PT.items():  # the x-height subtends 0.20 degrees at 322 mm
        x_mm = size * lg.x_height(name) * lg.SCREEN_MM / lg.PAGE_W_PT
        assert math.degrees(math.atan(x_mm / lg.DISTANCE_MM)) >= lg.VISUAL_ANGLE_DEG


def test_headings_and_title_are_above_the_body():
    assert lg.BODY_PT < lg.HEADING_PT < lg.TITLE_PT


@pytest.mark.parametrize("path, lang", CAROUSELS)
def test_every_glyph_of_the_carousel_meets_the_floor(path, lang):
    pdf = ROOT / path
    assert lg.pdf_violations(pdf) == []
    smallest = lg.pdf_minimum_by_style(pdf)
    assert smallest["regular"] == pytest.approx(lg.BODY_PT, abs=0.01)  # body sits on it


@pytest.mark.parametrize("lang", ["es", "en"])
def test_every_text_in_the_figures_meets_the_floor(lang):
    assert carousel.figure_violations(style.load_summary(RESULTS), lang) == []


@pytest.mark.parametrize("path, lang", CAROUSELS)
def test_previews_are_2_5_px_per_pt(path, lang):
    pngs = sorted((ROOT / path).parent.glob("slide-*.png"))
    assert pngs
    for png in pngs:
        assert Image.open(png).size == (lg.PREVIEW_PX, round(lg.PAGE_H_IN / lg.PAGE_W_IN
                                                              * lg.PREVIEW_PX))


def test_the_pdf_check_catches_small_type(tmp_path):
    src = tmp_path / "small.typ"
    src.write_text('#set text(font: "STIX Two Text", size: 15.8pt)\n'
                   '#show math.equation: set text(font: "STIX Two Math")\n'
                   "Body $x_1$ #text(12pt)[tiny] #emph[slanted]\n")
    pdf = tmp_path / "small.pdf"
    typst.compile(str(src), output=str(pdf), font_paths=[str(lg.FONTS)],
                  ignore_system_fonts=True)
    bad = lg.pdf_violations(pdf)
    assert any("'t'" in b and "12.00 pt regular" in b for b in bad)  # set small
    assert any("'1'" in b and " math" in b for b in bad)  # a subscript shrinks
    assert any("'s'" in b and "15.80 pt italic" in b for b in bad)  # italic needs 16.0
    assert not any("'B'" in b for b in bad)  # body at 15.8 passes


def test_the_figure_check_catches_small_type():
    style.paper_style()
    fig = carousel.plt.figure(figsize=(carousel.TEXT_W, 2.0))
    ax = fig.add_axes((0.2, 0.3, 0.6, 0.5))
    ax.set_xlabel("tiny", fontsize=12)
    ax.set_title("$x^2$")
    ax.text(0.5, 0.5, "slanted", fontsize=lg.BODY_PT, style="italic")
    ax.text(5, 0.5, "outside")
    bad = lg.figure_violations(fig, "t")
    carousel.plt.close(fig)
    assert any("'tiny'" in b and "12.00 pt regular" in b for b in bad)
    assert any("mathtext" in b for b in bad)
    assert any("'slanted'" in b and "italic" in b for b in bad)
    assert any("outside the canvas" in b for b in bad)
