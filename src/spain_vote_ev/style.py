"""The shared look of the figures and the carousel: a paper. STIX Two type (vendored in
fonts/), black and greys, and one brown accent that is no Spanish party's colour. Lists are
never told apart by colour: every list is drawn in the same ink."""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib import font_manager  # noqa: E402

FONTS = Path(__file__).parent / "fonts"
INK, GREY, LIGHT, FILL = "#000000", "#555555", "#9a9a9a", "#e2e2e2"
ACCENT = "#8c5a1e"  # a dark ochre-brown


def paper_style() -> None:
    for font in sorted(FONTS.glob("STIX2Text-*.otf")):
        font_manager.fontManager.addfont(str(font))
    plt.rcParams.update({
        "font.family": ["STIX Two Text", "STIXGeneral"],
        "font.size": 12,
        "mathtext.fontset": "stix",
        "text.color": INK,
        "figure.facecolor": "white",
        "axes.facecolor": "white",
        "savefig.facecolor": "white",
        "axes.edgecolor": INK,
        "axes.linewidth": 0.6,
        "axes.labelcolor": INK,
        "axes.labelsize": 12,
        "axes.grid": False,
        "axes.spines.top": True,
        "axes.spines.right": True,
        "xtick.direction": "in",
        "ytick.direction": "in",
        "xtick.top": True,
        "ytick.right": True,
        "xtick.major.size": 3.2,
        "ytick.major.size": 3.2,
        "xtick.minor.size": 1.8,
        "ytick.minor.size": 1.8,
        "xtick.major.width": 0.6,
        "ytick.major.width": 0.6,
        "xtick.labelsize": 11,
        "ytick.labelsize": 11,
        "xtick.color": INK,
        "ytick.color": INK,
        "legend.frameon": True,
        "legend.fancybox": False,
        "legend.edgecolor": INK,
        "legend.framealpha": 1.0,
        "legend.fontsize": 10.5,
        "patch.linewidth": 0.6,
        "hatch.linewidth": 0.5,
        "svg.fonttype": "path",
        "svg.hashsalt": "spain-vote-ev",
    })


def load_summary(results_dir: Path) -> dict:
    return json.loads((Path(results_dir) / "summary.json").read_text())
