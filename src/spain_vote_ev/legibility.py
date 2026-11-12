"""The type floor: the smallest type that reads at full speed on a phone, and the checks that
hold the carousel and its figures to it. Every type size in the carousel comes from here.

Criterion
---------
Critical print size. Reading speed stays at its maximum down to a critical print size and
drops below it. Legge and Bigelow (2011, "Does print size matter for reading? A review of
findings from vision science and typography", Journal of Vision 11(5):8,
doi:10.1167/11.5.8) put this lower end of the fluent range at an x-height of about 0.2
degrees of visual angle (from about 0.15 to 0.3 degrees, depending on the reader, the font
and the method), and newspaper running text at 0.20 to 0.26 degrees, read at 40 cm (their
Table 2). The floor is an x-height of 0.20 degrees.

Distance. 322 mm: the mean distance at which people read web pages on a smartphone
(Bababekova, Rosenfield, Hue and Huang, 2011, "Font size and viewing distance of handheld
smart phones", Optometry and Vision Science 88(7), 795-797, PubMed 21499163). The text their
participants chose averaged 0.8 M, an x-height of about 0.207 degrees at that distance:
consistent with the floor.

Screen. The narrowest common phone class, 6.1 inches: 1179 px at 460 ppi, 65.1 mm wide
(iPhone 15 and 16; Galaxy S24 65.9 mm, Pixel 9 65.0 mm). LinkedIn shows a carousel page
across the full width of the screen, so the 6-inch (432 pt) page is 65.1 mm wide.

x-height. Read from the vendored fonts (fonts/): OS/2 sxHeight / unitsPerEm. STIX Two Text
Regular, Bold and Bold Italic, and STIX Two Math: 0.473; Italic: 0.467.

Floor. A size s (pt) has an x-height of s * xh * 65.1 / 432 mm on the screen, which must be
at least 322 mm * tan(0.20 degrees) = 1.124 mm:

    min_pt(style) = 432 * 322 * tan(0.20 deg) / (xh(style) * 65.1)

15.77 pt for Regular (15.8, rounded up to 0.1 pt) and 15.97 pt for Italic (16.0). On the
1080-px previews, 2.5 px per pt.

Rules
-----
Body text is exactly the regular minimum, and nothing is smaller than its style's minimum:
captions, tables, notes, the running header, page numbers, references, equations, and every
text in the figures, which are drawn at the text width and embedded at 100%, so a figure's
points are the page's points. No subscripts or superscripts: they shrink. Headings and the
title are larger; there is no size below the body.

pdf_violations() reads every glyph of a PDF with pdfplumber; figure_violations() reads every
text artist of a matplotlib figure. Both flag a glyph below its style's minimum, a font that is
not one of the vendored ones (its x-height is unknown), and glyphs that are drawn small by
design (superscript and subscript characters, ordinal indicators).
"""

from __future__ import annotations

import math
import re
import unicodedata
from functools import cache
from pathlib import Path

from fontTools.ttLib import TTFont

FONTS = Path(__file__).parent / "fonts"

VISUAL_ANGLE_DEG = 0.20  # x-height at the critical print size (Legge and Bigelow, 2011)
CPS_RANGE_DEG = (0.15, 0.3)  # how it varies with the reader, the font and the method
DISTANCE_MM = 322.0  # mean distance for web pages on a smartphone (Bababekova et al., 2011)
PHONE_IN = 6.1  # the narrowest common class of phone, by screen diagonal
SCREEN_PX, SCREEN_PPI = 1179, 460  # its width: iPhone 15 and 16
SCREEN_MM = SCREEN_PX / SCREEN_PPI * 25.4  # 65.1 mm, the width the page is shown at
PAGE_W_IN, PAGE_H_IN = 6.0, 7.5  # the carousel page, 4:5
PAGE_W_PT = PAGE_W_IN * 72  # 432 pt across the screen
PREVIEW_PX = 1080  # width of the PNG previews

STYLE_FILES = {"regular": "STIX2Text-Regular.otf", "italic": "STIX2Text-Italic.otf",
               "bold": "STIX2Text-Bold.otf", "bolditalic": "STIX2Text-BoldItalic.otf",
               "math": "STIX2Math.otf"}


@cache
def _font(style: str) -> tuple[str, float, frozenset[int]]:
    """PostScript name, x-height ratio and the code points of a vendored font."""
    font = TTFont(FONTS / STYLE_FILES[style], lazy=True)
    xh = font["OS/2"].sxHeight / font["head"].unitsPerEm
    return font["name"].getDebugName(6), xh, frozenset(font.getBestCmap())


def x_height(style: str) -> float:
    """OS/2 sxHeight / unitsPerEm of the vendored font for a style."""
    return _font(style)[1]


def raw_min_pt(style: str) -> float:
    """The smallest size, in pt, whose x-height subtends VISUAL_ANGLE_DEG on the phone."""
    need_mm = DISTANCE_MM * math.tan(math.radians(VISUAL_ANGLE_DEG))
    return PAGE_W_PT * need_mm / (x_height(style) * SCREEN_MM)


def min_pt(style: str) -> float:
    """raw_min_pt rounded up to 0.1 pt: the size the carousel sets."""
    return math.ceil(round(raw_min_pt(style) * 10, 6)) / 10


MIN_PT = {style: min_pt(style) for style in STYLE_FILES}
BODY_PT = MIN_PT["regular"]  # 15.8: body, captions, tables, notes, references, figures
ITALIC_PT = MIN_PT["italic"]  # 16.0: anything set in italic
HEADING_PT = 18.5  # section headings, bold
TITLE_PT = 25.0  # the title on page 1, bold
PX_PER_PT = PREVIEW_PX / PAGE_W_PT  # 2.5 on the previews
TOLERANCE_PT = 0.005  # PDF coordinates are floats

# Characters that fonts draw small by design.
SHRUNK = re.compile(r"SUPERSCRIPT|SUBSCRIPT|MODIFIER LETTER SMALL|ORDINAL INDICATOR")


def facts() -> dict[str, float]:
    """The criterion's numbers, for the texts that quote them (see facts.build)."""
    return {"angle": VISUAL_ANGLE_DEG, "cps_low": CPS_RANGE_DEG[0],
            "cps_high": CPS_RANGE_DEG[1], "distance_mm": DISTANCE_MM, "phone_in": PHONE_IN,
            "screen_mm": SCREEN_MM, "screen_px": SCREEN_PX, "screen_ppi": SCREEN_PPI,
            "xh_regular": x_height("regular"), "xh_italic": x_height("italic"),
            "raw_regular": raw_min_pt("regular"), "raw_italic": raw_min_pt("italic"),
            "min_regular": MIN_PT["regular"], "min_italic": MIN_PT["italic"],
            "px_per_pt": PX_PER_PT}


def style_of(fontname: str) -> str | None:
    """The style of a font by its PostScript name, with or without a subset prefix
    (ABCDEF+STIXTwoText-Italic); None if it is not a vendored font."""
    base = fontname.split("+", 1)[-1]
    return {_font(s)[0]: s for s in STYLE_FILES}.get(base)


def shrunk(text: str) -> list[str]:
    """Characters in a text that are drawn small by design."""
    return [c for c in text if SHRUNK.search(unicodedata.name(c, ""))]


def _too_small(size: float, style: str) -> bool:
    return size < MIN_PT[style] - TOLERANCE_PT


# --- the PDF ----------------------------------------------------------------------------------


def pdf_glyphs(path: Path) -> list[dict]:
    """Every glyph of a PDF: page, character, font, style and size in pt (pdfplumber)."""
    import pdfplumber

    out = []
    with pdfplumber.open(path) as pdf:
        for n, page in enumerate(pdf.pages, start=1):
            for ch in page.chars:
                out.append({"page": n, "text": ch["text"], "font": ch["fontname"],
                            "style": style_of(ch["fontname"]), "size": float(ch["size"]),
                            "upright": bool(ch["upright"])})
    return out


def pdf_violations(path: Path) -> list[str]:
    """Glyphs of a PDF below their style's minimum, in an unknown font, rotated (their size
    cannot be read), or small by design."""
    out = []
    for g in pdf_glyphs(path):
        where = f"{Path(path).name} p. {g['page']} {g['text']!r}"
        if g["style"] is None:
            out.append(f"{where}: {g['font']} is not a vendored font")
        elif not g["upright"]:
            out.append(f"{where}: rotated")
        elif _too_small(g["size"], g["style"]):
            out.append(f"{where}: {g['size']:.2f} pt {g['style']}, minimum "
                       f"{MIN_PT[g['style']]} pt")
        if shrunk(g["text"]):
            out.append(f"{where}: drawn small by design")
    return out


def pdf_minimum_by_style(path: Path) -> dict[str, float]:
    """The smallest glyph size found in a PDF, per style."""
    out: dict[str, float] = {}
    for g in pdf_glyphs(path):
        key = g["style"] or g["font"]
        out[key] = min(out.get(key, math.inf), g["size"])
    return out


# --- the figures ------------------------------------------------------------------------------

MATHTEXT = re.compile(r"(?<!\\)\$.*(?<!\\)\$")


def _figure_style(text) -> str | None:
    from matplotlib import font_manager

    path = Path(font_manager.findfont(text.get_fontproperties(), fallback_to_default=False))
    by_path = {(FONTS / f).resolve(): s for s, f in STYLE_FILES.items()}
    return by_path.get(path.resolve())


def figure_violations(fig, name: str = "figure") -> list[str]:
    """Text artists of a matplotlib figure below their style's minimum, in a font that is not
    vendored, with glyphs the font lacks (they would come from a fallback font), with mathtext
    (its scripts shrink and it uses other fonts), or outside the canvas (they would be cut)."""
    from matplotlib.text import Text

    fig.canvas.draw()
    out = []
    for t in fig.findobj(Text):
        text = t.get_text()
        if not text.strip():
            continue
        where = f"{name}: {text!r}"
        style = _figure_style(t)
        if style is None:
            out.append(f"{where}: not a vendored font")
            continue
        if _too_small(t.get_fontsize(), style):
            out.append(f"{where}: {t.get_fontsize():.2f} pt {style}, minimum {MIN_PT[style]} pt")
        if MATHTEXT.search(text):
            out.append(f"{where}: mathtext")
        missing = sorted({c for c in text if not c.isspace() and ord(c) not in _font(style)[2]})
        if missing:
            out.append(f"{where}: {''.join(missing)!r} not in the {style} font")
        if shrunk(text):
            out.append(f"{where}: drawn small by design")
    renderer = fig.canvas.get_renderer()
    tight, canvas = fig.get_tightbbox(renderer), fig.bbox_inches
    slack = 0.5 / 72
    if (tight.x0 < canvas.x0 - slack or tight.y0 < canvas.y0 - slack
            or tight.x1 > canvas.x1 + slack or tight.y1 > canvas.y1 + slack):
        out.append(f"{name}: drawn outside the canvas ({tight.bounds} beyond {canvas.bounds})")
    return out
