import re

import pytest

from spain_vote_ev import style, tables, texts
from spain_vote_ev.sources import RESULTS


@pytest.fixture(scope="module")
def summary():
    return style.load_summary(RESULTS)


def test_every_table_renders(summary):
    from spain_vote_ev import facts
    f = facts.build(summary)
    for name, make in tables.BLOCKS.items():
        out = make(summary, f)
        assert out.strip(), name


def test_templates_fill_every_slot(summary):
    for name, lang in texts.TEXTS.items():
        out = texts.render((texts.TEMPLATES / name).read_text(), summary, lang)
        assert not texts.SLOT.search(out), name
        assert not re.search(r"\{\{|\}\}", out), name


def test_unknown_slot_is_an_error(summary):
    with pytest.raises(KeyError):
        texts.render("{{no.such.fact}}", summary, "en")


def test_language_switches_midway(summary):
    out = texts.render("{{seat.one_in}}\n<!-- lang: es -->\n{{seat.one_in}}", summary, "en")
    first, second = out.split("<!-- lang: es -->")
    assert "," in first.strip() and "." in second.strip()
