"""The investiture record (data/curated/investitures.csv) and what the texts say about it."""

from spain_vote_ev import facts as fx
from spain_vote_ev import parties, prepare


def test_the_rules_pass_exactly_the_votes_that_passed():
    record = prepare.record()  # raises if a vote's groups do not add up to its totals or to 350
    passed = [(v["date"], v["candidate"].split()[-1]) for v in record if v["passed"]]
    assert passed == [("2016-10-29", "Rajoy"), ("2018-06-01", "Sánchez"),
                      ("2020-01-07", "Sánchez"), ("2023-11-16", "Sánchez")]


def test_the_2023_votes_match_the_base_rule():
    record = {(v["date"], v["round"]): v for v in prepare.record()}
    for date, who in (("2023-09-27", "feijoo"), ("2023-11-16", "sanchez")):
        vote = record[(date, 1)]
        yes = {g["party"]: g["yes"] for g in vote["groups"] if g["yes"]}
        base = parties.INVESTITURES[who]
        assert (vote["yes"], vote["no"], vote["abstain"]) == (base["yes"], base["no"], 0)
        assert sum(yes.values()) == sum(base["yes_by_party"].values())


def test_abstentions_that_decided_are_named():
    record = prepare.record()
    f, e = {}, {}
    fx._record_facts(f, fx.Fmt("en"), record)
    fx._record_facts(e, fx.Fmt("es"), record)
    assert f["rec.decided"] == "October 2016 and January 2020"
    assert e["rec.decided"] == "octubre de 2016 y enero de 2020"
    assert f["rec.last.abstained"] == "nobody abstained"
