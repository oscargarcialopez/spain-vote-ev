from pathlib import Path

import pytest

from spain_vote_ev import facts, style
from spain_vote_ev.sources import RESULTS, ROOT


@pytest.mark.parametrize("x, text", [
    (76_433.96, "76,000"), (10_765_236.5, "10.8 million"), (60_000_000, "60 million"),
    (13_983_816, "14 million"), (1_076_523_646, "1.1 billion"), (92.77, "93"), (4.6386, "4.6"),
])
def test_sig(x, text):
    assert facts.sig(x) == text


def test_numbers_in_reads_what_a_reader_reads():
    text = ("1 in 76,000 and 1 in 10.8 million (3.2%); 84,2 % in Spanish; 22 of 26.\n"
            "Not claims: `code 123`, 2026-11-29, BOE-A-2026-23103, SHA-256, "
            "[link](https://example.org/987), github.com/x/y-42, version 1.2.3.\n"
            "## References\n\nSomeone (1999). 45(6), 7–89.")
    assert facts.numbers_in(text) == ["1", "76000", "1", "10.8", "3.2", "84.2", "22", "26"]


def test_check_flags_numbers_not_in_the_results():
    f = {"a": "1 in 76,000", "b": "10.8 million"}
    assert facts.check("1 in 76,000 or 1 in 10.8 million", f) == []
    assert facts.check("1 in 75,000, 176 seats, 33.3%", f) == ["33.3", "75000"]


def test_published_texts_match_the_results():
    """README.md, POST.md and the carousel quote only numbers from results/summary.json."""
    paths = [ROOT / p for p in ("README.md", "POST.md", "carousel/slides.txt")]
    assert all(Path(p).exists() for p in paths)
    assert facts.check_files(paths, style.load_summary(RESULTS)) == 0
