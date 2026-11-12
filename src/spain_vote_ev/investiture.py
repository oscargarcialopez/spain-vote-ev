"""Who is invested after the election: the investiture vote of art. 99 of the Constitution.

Rules (Constitución, art. 99; Reglamento del Congreso, arts. 170-172). After consulting the
groups, the King proposes a candidate through the Speaker. The candidate is invested in a first
vote with the absolute majority of the 350 deputies (176 yes); otherwise in a second vote 48
hours later with more yes than no votes. Further proposals may follow; if no candidate has
been invested two months after the first vote, both chambers are dissolved and a new election
is called.

Who votes how. Two candidates are proposed: the PP's and the PSOE's. Base rule: each 2026 list
votes as its group voted in the two investitures of the 2023 legislature, on the PP's candidate
as on Feijóo's (27 Sep 2023) and on the PSOE's candidate as on Sánchez's (16 Nov 2023), with
no abstentions, as then. A list inherits the vote of the 2023 group it comes from: PP's lists
include UPN (UPN-PP in Navarra); Frente Amplio and Podemos sat in the Sumar group. Lists with
no seat in 2023 (SALF, Adelante Andalucía, Teruel Existe, Soria ¡Ya!) have no record and vote
no; a sensitivity has them abstain. Under the base rule nobody abstains, so the second vote
needs 176 too, and a candidate is invested exactly when its 2023 coalition has 176 seats.

Order. If both candidates could be invested (only possible when Coalición Canaria, which voted
yes to both in 2023, holds the balance), the candidate of the larger party is proposed first,
as in 2023; a tie in seats goes to the PP's candidate. This is an assumption, and a rare case
(summary.json reports how rare).

The votes needed ("la llave"): a list's votes are necessary for an investiture if, had the list
voted no instead of yes, the candidate would have lost both votes.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from . import parties

MAJORITY = parties.MAJORITY
CANDIDATES = ("PP", "PSOE")  # the PP's candidate and the PSOE's candidate
RECORD_EVENT = {"PP": "feijoo", "PSOE": "sanchez"}  # the 2023 vote each one repeats
# 2026 list -> the 2023 group whose vote it inherits.
GROUP_2023 = {"PP": "PP", "PSOE": "PSOE", "VOX": "VOX", "FA": "SUMAR", "PODEMOS": "SUMAR",
              "ERC": "ERC", "JUNTS": "JUNTS", "BILDU": "BILDU", "PNV": "PNV", "BNG": "BNG",
              "CC": "CC"}
BLOCKED, FIRST, SECOND = 0, 1, 2  # codes of `who`: nobody, the PP's, the PSOE's candidate


def record_2023(candidate: str) -> dict[str, str]:
    """'yes' or 'no' of each 2023 group in the 2023 vote the candidate repeats. Every deputy
    voted, so a group that did not vote yes voted no (172 + 178 and 179 + 171 = 350)."""
    vote = parties.INVESTITURES[RECORD_EVENT[candidate]]
    assert vote["yes"] + vote["no"] == 350, "the 2023 votes had no abstentions"
    groups = set(parties.SEATS_2023)
    return {g: "yes" if g in vote["yes_by_party"] else "no" for g in groups}


@dataclass(frozen=True)
class Behaviour:
    """Yes and no votes of every list on each candidate; a list in neither abstains."""
    name: str
    labels: tuple[str, ...]
    yes: np.ndarray    # (C, K) bool
    no: np.ndarray     # (C, K) bool
    party: np.ndarray  # (C,) index of each candidate's own list in labels

    def table(self) -> dict[str, dict[str, str]]:
        out = {}
        for c, cand in enumerate(CANDIDATES):
            out[cand] = {lab: "yes" if self.yes[c, k] else "no" if self.no[c, k] else "abstain"
                         for k, lab in enumerate(self.labels) if lab not in ("OTH", "BLANK")}
        return out


def behaviour(labels: list[str], no_record: str = "no",
              overrides: dict[tuple[str, str], str] | None = None,
              name: str = "base") -> Behaviour:
    """The base rule, with the lists without a 2023 record voting `no_record`, and any
    (candidate, list) -> vote overrides."""
    if no_record not in ("no", "abstain"):
        raise ValueError(no_record)
    overrides = overrides or {}
    C, K = len(CANDIDATES), len(labels)  # noqa: N806
    yes, no = np.zeros((C, K), bool), np.zeros((C, K), bool)
    for c, cand in enumerate(CANDIDATES):
        rec = record_2023(cand)
        for k, lab in enumerate(labels):
            if lab in ("OTH", "BLANK"):
                continue
            vote = rec[GROUP_2023[lab]] if lab in GROUP_2023 else no_record
            vote = overrides.get((cand, lab), vote)
            yes[c, k], no[c, k] = vote == "yes", vote == "no"
    party = np.array([labels.index(c) for c in CANDIDATES])
    return Behaviour(name, tuple(labels), yes, no, party)


def outcome(yes: np.ndarray, no: np.ndarray, party_seats: np.ndarray
            ) -> tuple[np.ndarray, np.ndarray]:
    """yes, no, party_seats: (..., C). Returns who is invested (BLOCKED, FIRST, SECOND: the
    PP's or the PSOE's candidate) and in which vote (1 or 2; 0 if nobody)."""
    first_vote = yes >= MAJORITY
    passes = first_vote | (yes > no)
    both = passes[..., 0] & passes[..., 1]
    larger = np.where(party_seats[..., 1] > party_seats[..., 0], SECOND, FIRST)
    who = np.where(both, larger, np.where(passes[..., 0], FIRST,
                                          np.where(passes[..., 1], SECOND, BLOCKED)))
    c = np.clip(who - 1, 0, 1)
    in_first = np.take_along_axis(first_vote, c[..., None], axis=-1)[..., 0]
    stage = np.where(who == BLOCKED, 0, np.where(in_first, 1, 2))
    return who.astype(np.int8), stage.astype(np.int8)


def tallies(seats: np.ndarray, b: Behaviour) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """seats (m, K) -> yes, no and the candidates' own seats, each (m, C)."""
    s = seats.astype(np.int32)
    return s @ b.yes.T.astype(np.int32), s @ b.no.T.astype(np.int32), s[:, b.party]


def necessary(seats: np.ndarray, b: Behaviour, who: np.ndarray) -> np.ndarray:
    """(m, K) bool: the list voted yes for the invested candidate, and with its seats voting no
    instead the candidate would have lost both votes."""
    yes, no, _ = tallies(seats, b)
    c = np.clip(who.astype(int) - 1, 0, 1)
    rows = np.arange(len(who))
    y, n_ = yes[rows, c][:, None], no[rows, c][:, None]
    s = seats.astype(np.int32)
    voted_yes = b.yes[c]  # (m, K)
    lose = ((y - s) < MAJORITY) & ((y - s) <= (n_ + s))
    return (who[:, None] != BLOCKED) & voted_yes & (s > 0) & lose


def after_transfer(yes: np.ndarray, no: np.ndarray, own: np.ndarray, b: Behaviour,
                   loser: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """The tallies if each list k took one seat from loser[:, k]: (m, K, C) each."""
    Y, N = b.yes.T.astype(np.int32), b.no.T.astype(np.int32)  # noqa: N806  (K, C)
    gain_y, lose_y = Y[None, :, :], Y[loser]
    gain_n, lose_n = N[None, :, :], N[loser]
    K = loser.shape[1]  # noqa: N806
    k = np.arange(K)[None, :, None]
    own_new = own[:, None, :] + (k == b.party[None, None, :]) - \
        (loser[:, :, None] == b.party[None, None, :])
    return (yes[:, None, :] + gain_y - lose_y, no[:, None, :] + gain_n - lose_n, own_new)
