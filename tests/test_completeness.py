"""Every 2026 candidacy left in 'others' is far from a seat (completeness.py)."""

from spain_vote_ev import completeness


def test_names_match_across_elections():
    assert completeness.same_list("GEROA BAI (GBAI)", "GBAI", "COALICIÓN «GEROA BAI»", "")
    assert not completeness.same_list("FRENTE OBRERO (FO)", "FO", "GEROA BAI", "GBAI")


def test_no_list_left_in_others_has_won_a_winning_share():
    r = completeness.check()
    assert r["flagged"] == []
    assert r["poll_columns_below_min_firms"] == {}
