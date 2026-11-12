from pathlib import Path

import pytest

from spain_vote_ev import facts, style
from spain_vote_ev.cli import CHECKED
from spain_vote_ev.sources import RESULTS, ROOT

NB = facts.NBSP


@pytest.mark.parametrize("x, text", [
    (76_433.96, "76,000"), (10_765_236.5, "10.8 million"), (60_000_000, "60 million"),
    (13_983_816, "14 million"), (1_076_523_646, "1.1 billion"), (92.77, "93"), (4.6386, "4.6"),
])
def test_sig(x, text):
    assert facts.sig(x) == text


@pytest.mark.parametrize("x, text", [
    (76_433.96, "76.000"), (10_765_236.5, "10,8 millones"), (60_000_000, "60 millones"),
    (13_983_816, "14 millones"), (1_076_523_646, "1.100 millones"), (92.77, "93"),
    (4.6386, "4,6"), (1_234.5, "1.200"),
])
def test_sig_in_spanish(x, text):
    assert facts.Fmt("es").sig(x) == text


def test_spanish_formats():
    es, en = facts.Fmt("es"), facts.Fmt("en")
    assert es.pct(0.9423, 1) == f"94,2{NB}%" and en.pct(0.9423, 1) == "94.2%"
    assert es.euros(380_400) == f"380.000{NB}€" and en.euros(380_400) == "380,000 €"
    assert es.euros(53_812_345) == "53,8 millones de euros"
    assert en.euros(53_812_345) == "53.8 million €"
    assert es.date("2026-11-29") == "29 de noviembre de 2026"
    assert en.date("2026-11-29") == "29 November 2026"
    assert es.period("2026-10-27", "2026-11-10") == "del 27 de octubre al 10 de noviembre de 2026"
    assert en.period("2026-10-27", "2026-11-10") == "27 October – 10 November 2026"
    assert (es.between("2026-10-27", "2026-11-10")
            == "entre el 27 de octubre y el 10 de noviembre de 2026")
    assert es.of(22, 26) == "22 de 26" and es.signed(-10.71) == "−10,7"
    assert es.num(13_983_816) == "13.983.816"


def test_numbers_in_reads_what_a_reader_reads():
    text = ("1 in 76,000 and 1 in 10.8 million (3.2%); 22 of 26.\n"
            "Not claims: `code 123`, 2026-11-29, BOE-A-2026-23103, SHA-256, art. 69.7, "
            "[link](https://example.org/987), github.com/x/y-42, version 1.2.3.\n"
            "## References\n\nSomeone (1999). 45(6), 7–89.")
    assert facts.numbers_in(text) == ["1", "76000", "1", "10.8", "3.2", "22", "26"]


def test_numbers_in_reads_spanish():
    text = (f"1 entre 76.000 y 1 entre 10,8 millones (94,2{NB}%); 22 de 26, en 2026; "
            f"art. 69.7 de la LOREG; 1.100 millones; 5{NB}€.\n"
            "## Referencias\n\nAlguien (1999). 45(6), 7–89.")
    assert facts.numbers_in(text, "es") == ["1", "76000", "1", "10.8", "94.2", "22", "26",
                                            "2026", "1100", "5"]


def test_check_flags_numbers_not_in_the_results():
    f = {"a": "1 in 76,000", "b": "10.8 million"}
    assert facts.check("1 in 76,000 or 1 in 10.8 million", f) == []
    assert facts.check("1 in 75,000, 176 seats, 33.3%", f) == ["33.3", "75000"]


def test_check_flags_numbers_in_the_wrong_format():
    en = {"a": "1 in 76,000", "b": "10.8 million"}
    es = {"a": "1 entre 76.000", "b": "10,8 millones", "c": f"94,2{NB}%"}
    assert facts.check("1 entre 76.000 o 1 entre 10,8 millones", es, "es") == []
    assert facts.check(f"1 in 76,000, 84,2{NB}%", en) == ["84,2 (not en number format)"]
    assert facts.check("1 in 76000", en) == ["76000 (needs a thousands separator)"]
    assert facts.check("1080 by 1350", en) == []  # English groups from five digits
    assert facts.check("seed 20261129", en) == ["20261129",
                                                "20261129 (needs a thousands separator)"]
    assert facts.check("10.8 millones", es, "es") == ["10.8 (not es number format)"]
    assert facts.check("1 entre 76000", es, "es") == ["76000 (needs a thousands separator)"]
    assert facts.check("en 2026", es, "es") == []
    assert facts.check("94,2%", es, "es") == ["94,2% (no-break space before %)"]
    assert facts.check("94,2 %", es, "es") == ["94,2 % (no-break space before %)"]
    assert facts.check(f"94,2{NB}%", es, "es") == []


def test_segments_switch_language():
    text = "a 1,5\n<!-- lang: en -->\nb 1.5\n"
    assert facts.segments(text, "es") == [("es", "a 1,5\n"), ("en", "\nb 1.5\n")]
    summary = style.load_summary(RESULTS)
    count, problems = facts.check_text(text.replace("1,5", "1").replace("1.5", "2"), summary,
                                       "es")
    assert (count, problems) == (2, [])


def test_published_texts_match_the_results():
    """README.md, POST.md and both carousels quote only numbers from results/summary.json."""
    paths = [(ROOT / p, lang) for p, lang in CHECKED]
    assert all(Path(p).exists() for p, _ in paths)
    assert facts.check_files(paths, style.load_summary(RESULTS)) == 0
