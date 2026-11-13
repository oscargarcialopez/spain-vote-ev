"""README.md and POST.md, written from their templates (src/spain_vote_ev/templates/) with the
numbers of results/summary.json, so that a rerun rewrites every number and every word that
depends on one (such as "close to the odds of" in facts.compare).

In a template, {{key}} is facts[key] (facts.build) in the language of that part of the
template, and {{table:name}} is one of the README's tables (tables.BLOCKS, in English). The
README is English and the post Spanish; a line `<!-- lang: xx -->` switches language for what
follows, the same mark `voteev check` reads. An unknown key is an error: a template cannot
quote a number that summary.json does not have.
"""

from __future__ import annotations

import re
from pathlib import Path

from . import facts as fx
from . import tables
from .sources import ROOT

TEMPLATES = Path(__file__).parent / "templates"
TEXTS = {"README.md": "en", "POST.md": "es"}
SLOT = re.compile(r"\{\{\s*([^{}]+?)\s*\}\}")
HEADER = ("<!-- Written by `voteev texts` from src/spain_vote_ev/templates/{name}, with the "
          "numbers of results/summary.json. Edit the template, not this file. -->\n")


def render(template: str, s: dict, lang: str) -> str:
    """The template with every slot filled, each part in its language."""
    built: dict[str, dict[str, str]] = {}

    def facts(lg: str) -> dict[str, str]:
        if lg not in built:
            built[lg] = fx.build(s, lg)
        return built[lg]

    def fill(text: str, lg: str) -> str:
        def one(m: re.Match) -> str:
            key = m.group(1)
            if key.startswith("table:"):
                return tables.BLOCKS[key.removeprefix("table:")](s, facts("en"))
            if key not in facts(lg):
                raise KeyError(f"{{{{{key}}}}}: no such fact in {lg}")
            return facts(lg)[key]
        return SLOT.sub(one, text)

    out, pos = [], 0
    for m in fx.LANG_MARK.finditer(template):
        out += [fill(template[pos:m.start()], lang), m.group()]
        lang, pos = m.group(1), m.end()
    out.append(fill(template[pos:], lang))
    return "".join(out)


def write(s: dict, root: Path = ROOT) -> list[Path]:
    done = []
    for name, lang in TEXTS.items():
        text = render((TEMPLATES / name).read_text(), s, lang)
        (Path(root) / name).write_text(HEADER.format(name=name) + text)
        done.append(Path(root) / name)
    return done
