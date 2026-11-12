"""The model: from the poll median to simulated elections, constituency by constituency.

1. National shares. Each polling firm's latest poll whose fieldwork ended in the 14 days up to
   the cutoff; the median across firms of each list's share. A list counts as polled when at
   least MIN_FIRMS firms report it; otherwise it keeps its base-election share. Blank votes and
   unlabelled lists keep their base share too, and the polled shares are rescaled to fill the
   rest.
2. National error. In each simulation every polled share moves on the logit scale by a normal
   error whose standard deviation is the root mean square of the same median's past errors
   (actual result minus median, logit scale, lists with at least 1%), measured at the same
   number of days before the election. Errors are centred on zero. Rescaling the shares to sum
   to one makes them negatively correlated; the past errors show no positive correlation within
   blocs to add (calibration.json reports the check).
3. Constituencies. Proportional swing: a list's share in a constituency is its base share times
   its national ratio (simulated share / base share), times exp(δ), then shares are rescaled
   to one in each constituency and raked so that national totals equal the simulated ones.
   δ = CCAA effect + constituency effect, both normal, with variances estimated from how
   provincial swings departed from national swings between consecutive elections.
4. Turnout. The base election's turnout per constituency, moved by a national and a
   constituency logit error estimated from past changes; valid votes per voter as in the base.
5. Seats. D'Hondt with the 3% threshold in every constituency (dhondt.py), and for each list
   the extra votes it needs for one more seat (Δ) and which list would lose that seat.

One more vote. P(one extra vote for list p in constituency i changes a seat) is the density of
Δ at zero, estimated as #(0 < Δ ≤ h) / (n h), with h a fixed fraction of the constituency's
quota (expected valid votes / seats); results are reported for three bandwidths. The same count
restricted to simulations where that seat changes whether a bloc reaches 176 gives the
probability of changing the majority.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import date, timedelta
from functools import cache

import numpy as np
import pandas as pd
from scipy.special import expit, logit

from . import dhondt, parties, polls
from .provinces import CCAA, CODES
from .sources import ELECTION_DATE, ELECTIONS, PROCESSED

NONSEAT = ("OTH", "BLANK")
MIN_FIRMS = 5          # firms that must report a list for it to count as polled
MIN_SHARE = 0.01       # lists below 1% are left out of the error calibrations
H_MULTS = (0.01, 0.02, 0.05)  # bandwidths, as fractions of the constituency's quota
H_DEFAULT = 0.02
RAKE_ITERS = 15
SEED = 20261129


@dataclass(frozen=True)
class Target:
    key: str
    base: str
    families: tuple[str, ...]
    base_map: dict[str, tuple[str, ...]]
    poll_spec: dict[str, dict] = field(default_factory=dict)
    result_map: dict[str, tuple[str, ...]] | None = None
    drop: tuple[str, ...] = ()   # base labels whose voters are spread over the rest
    new: tuple[str, ...] = ()    # lists with no base: the same share wherever they run


def _same(*fams: str) -> dict[str, tuple[str, ...]]:
    return {f: (f,) for f in fams}


TARGETS: dict[str, Target] = {
    # The forecast. Sumar's 2023 vote is split between Frente Amplio and Podemos by their
    # ratio in the 2024 European election wherever both run in 2026 (build_2026_base).
    "2026": Target(
        "2026", "2023",
        families=("PP", "PSOE", "VOX", "FA", "PODEMOS", "SALF", "AA", "ERC", "JUNTS", "BILDU",
                  "PNV", "BNG", "CC", "TE", "SY"),
        base_map={"PP": ("PP", "UPN"),
                  **_same("PSOE", "VOX", "ERC", "JUNTS", "BILDU", "PNV", "BNG", "CC", "TE", "SY")},
        poll_spec={"FA": {"cols": ["FA", "FV"], "joint": "FA+FV"}},
        drop=("CUP", "AA", "SUMAR", "NC"),
        new=("AA",)),
    # Backtests: the same method, run as it would have been a week before each election.
    "2023": Target(
        "2023", "2019N",
        families=("PP", "PSOE", "VOX", "SUMAR", "ERC", "JUNTS", "BILDU", "PNV", "BNG", "CC",
                  "CUP", "TE"),
        base_map={"PP": ("PP", "NAS"), "SUMAR": ("UP", "MP"),
                  **_same("PSOE", "VOX", "ERC", "JUNTS", "BILDU", "PNV", "BNG", "CC", "CUP",
                          "TE")},
        poll_spec={"PP": {"cols": ["PP"], "fill": ["UPN"]}},
        result_map={"PP": ("PP", "UPN"),
                    **_same("PSOE", "VOX", "SUMAR", "ERC", "JUNTS", "BILDU", "PNV", "BNG",
                            "CC", "CUP", "TE")},
        drop=("CS", "PRC")),
    "2019N": Target(
        "2019N", "2019A",
        families=("PP", "PSOE", "VOX", "CS", "UP", "MP", "ERC", "JUNTS", "PNV", "BILDU", "BNG",
                  "CC", "CUP", "PRC"),
        base_map={"PP": ("PP", "NAS"), "CC": ("CC", "NC"),
                  **_same("PSOE", "VOX", "CS", "UP", "ERC", "JUNTS", "PNV", "BILDU", "BNG",
                          "PRC")},
        poll_spec={"PP": {"cols": ["PP"], "fill": ["NAS"]}},
        result_map={"PP": ("PP", "NAS"),
                    **_same("PSOE", "VOX", "CS", "UP", "MP", "ERC", "JUNTS", "PNV", "BILDU",
                            "BNG", "CC", "CUP", "PRC")},
        drop=("COMPROMIS",),
        new=("MP", "CUP")),
}

# Blocs whose majority status is tracked. 2026: the two 2023 investiture coalitions
# (parties.py). Backtests: the coalitions that voted for the investiture that followed.
BLOCS: dict[str, dict[str, tuple[str, ...]]] = {
    "2026": {"F": parties.BLOC_F, "S": parties.BLOC_S, "S_no_JUNTS": parties.BLOC_S_NO_JUNTS},
    "2023": {"F": ("PP", "VOX", "CC"),
             "S": ("PSOE", "SUMAR", "ERC", "JUNTS", "BILDU", "PNV", "BNG", "CC")},
    "2019N": {"S": ("PSOE", "UP", "PNV", "MP", "BNG")},
}


# --- data ---------------------------------------------------------------------------------------


@cache
def data() -> dict:
    d = {name: pd.read_csv(PROCESSED / f"{name}.csv", dtype={"code": str})
         for name in ("results", "summary", "ep2024", "constituencies_2026",
                      "candidacies_2026", "poll_results")}
    d["polls"] = pd.read_csv(PROCESSED / "polls.csv")
    d["context"] = json.loads((PROCESSED / "context.json").read_text())
    return d


def summary(election: str) -> pd.DataFrame:
    s = data()["summary"]
    return s[s["election"] == election].set_index("code").loc[CODES]


def shares(election: str) -> pd.DataFrame:
    """Votes of each label / valid votes, by constituency (CODES order); 'BLANK' included."""
    r = data()["results"]
    r = r[r["election"] == election]
    votes = r.pivot_table(index="code", columns="label", values="votes", aggfunc="sum",
                          fill_value=0).reindex(CODES, fill_value=0)
    summ = summary(election)
    votes["BLANK"] = summ["blank"]
    return votes.div(summ["valid"], axis=0)


def ep_shares() -> pd.DataFrame:
    ep = data()["ep2024"]
    votes = ep.pivot_table(index="code", columns="label", values="votes", aggfunc="sum",
                           fill_value=0).reindex(CODES, fill_value=0)
    return votes.div(votes.sum(axis=1), axis=0)


@cache
def poll_wide(election: str) -> pd.DataFrame:
    long = data()["polls"]
    g = long[long["election"] == election]
    meta = g.drop_duplicates("poll")[["poll", *polls.META]].copy()
    meta["end"] = pd.to_datetime(meta["end"]).dt.date
    wide = g.pivot(index="poll", columns="party", values="share").reset_index()
    return meta.merge(wide, on="poll")


def latest_poll_date(election: str) -> date:
    return max(poll_wide(election)["end"])


# --- the poll summary -----------------------------------------------------------------------


def _family_values(window: pd.DataFrame, spec: dict) -> list[float]:
    """One value per firm: the joint column if the firm polled the lists together, else the
    sum of the columns; small partner lists a firm leaves out ('fill') take the median of the
    firms that report them."""
    fills = {c: float(window[c].median()) if c in window and window[c].notna().any() else 0.0
             for c in spec.get("fill", [])}
    out = []
    for _, row in window.iterrows():
        joint = spec.get("joint")
        if joint and joint in row and pd.notna(row[joint]):
            v = float(row[joint])
        else:
            parts = [row.get(c, np.nan) for c in spec["cols"]]
            if any(pd.isna(p) for p in parts):
                continue
            v = float(sum(parts))
        for c, fill in fills.items():
            v += float(row[c]) if c in row and pd.notna(row[c]) else fill
        out.append(v)
    return out


def poll_summary(target: Target, cutoff: date, exclude_firms: tuple[str, ...] = ()
                 ) -> tuple[pd.DataFrame, dict[str, dict]]:
    wide = poll_wide(target.key)
    window = polls.window(wide[~wide["firm"].isin(exclude_firms)], cutoff)
    out = {}
    for f in target.families:
        spec = target.poll_spec.get(f, {"cols": [f]})
        vals = _family_values(window, spec)
        if len(vals) >= MIN_FIRMS:
            out[f] = {"median": float(np.median(vals)), "firms": len(vals),
                      "min": float(min(vals)), "max": float(max(vals))}
    return window, out


# --- the setup of one election ------------------------------------------------------------------


@dataclass
class Setup:
    key: str
    families: list[str]
    labels: list[str]
    codes: list[str]
    ccaa: np.ndarray
    n_ccaa: int
    seats: np.ndarray
    electors: np.ndarray
    turnout: np.ndarray
    valid_ratio: np.ndarray
    base: np.ndarray
    present: np.ndarray
    weights: np.ndarray
    base_national: np.ndarray
    national: np.ndarray
    polled: np.ndarray
    cutoff: date
    lead: int
    window: pd.DataFrame
    poll_medians: dict
    actual_seats: np.ndarray | None = None
    actual_shares: np.ndarray | None = None

    @property
    def F(self) -> int:
        return len(self.families)

    def idx(self, label: str) -> int:
        return self.labels.index(label)


def _presence_2026(labels: list[str]) -> np.ndarray:
    c = data()["candidacies_2026"].copy()
    c["label"] = c["label"].replace({"FV": "FA"})
    pres = np.zeros((len(CODES), len(labels)), bool)
    for k, lab in enumerate(labels):
        if lab in NONSEAT:
            pres[:, k] = True
        else:
            pres[:, k] = np.isin(CODES, c.loc[c["label"] == lab, "code"].unique())
    return pres


def _target_results(target: Target, labels: list[str]) -> tuple[np.ndarray, np.ndarray,
                                                                 np.ndarray]:
    """Presence, seats (I, K) and votes (I, K) of the target's own result, by family."""
    r = data()["results"]
    r = r[r["election"] == target.key]
    inv = {lab: fam for fam, labs in target.result_map.items() for lab in labs}
    r = r.assign(fam=r["label"].map(lambda x: inv.get(x, "OTH")))
    votes = r.pivot_table(index="code", columns="fam", values="votes", aggfunc="sum",
                          fill_value=0).reindex(index=CODES, columns=labels, fill_value=0)
    seats = r.pivot_table(index="code", columns="fam", values="seats", aggfunc="sum",
                          fill_value=0).reindex(index=CODES, columns=labels, fill_value=0)
    votes["BLANK"] = summary(target.key)["blank"]
    pres = votes.to_numpy() > 0
    pres[:, labels.index("OTH")] = True
    pres[:, labels.index("BLANK")] = True
    return pres, seats.to_numpy(), votes.to_numpy()


def build(key: str, cutoff: date | None = None, lead: int | None = None,
          exclude_firms: tuple[str, ...] = ()) -> Setup:
    target = TARGETS[key]
    ed = date.fromisoformat(ELECTION_DATE[key])
    if cutoff is None:
        cutoff = ed - timedelta(days=lead) if lead is not None else latest_poll_date(key)
    lead = (ed - cutoff).days
    labels = [*target.families, *NONSEAT]
    K = len(labels)
    base_sh = shares(target.base)
    summ_b = summary(target.base)
    turnout = (summ_b["voters"] / summ_b["electors"]).to_numpy()
    valid_ratio = (summ_b["valid"] / summ_b["voters"]).to_numpy()
    actual_seats = actual_shares = None
    if key == "2026":
        const = data()["constituencies_2026"].set_index("code").loc[CODES]
        seats, electors = const["seats"].to_numpy(), const["electors"].to_numpy()
        present = _presence_2026(labels)
    else:
        present, act_seats, act_votes = _target_results(target, labels)
        seats = act_seats.sum(axis=1)
        electors = summary(key)["electors"].to_numpy()
        actual_seats = act_seats[:, :len(target.families)]
        actual_shares = act_votes.sum(axis=0) / summary(key)["valid"].sum()

    inv = {lab: fam for fam, labs in target.base_map.items() for lab in labs}
    b = np.zeros((len(CODES), K))
    for lab in base_sh.columns:
        col = base_sh[lab].to_numpy()
        if lab == "BLANK":
            b[:, labels.index("BLANK")] += col
        elif lab in inv:
            b[:, labels.index(inv[lab])] += col
        elif lab not in target.drop:
            b[:, labels.index("OTH")] += col
    weights = electors * turnout * valid_ratio
    if key == "2026":
        b = _base_2026(b, present, base_sh, labels, weights)
    for f in target.new:
        b[:, labels.index(f)] = 1.0
    b = b * present
    # A national list running where its base is zero (and no rule above applies) takes its
    # mean base share where it has one. Local lists (a base in fewer than 5 constituencies)
    # get nothing where they did not run before.
    for k in range(K):
        miss = present[:, k] & (b[:, k] <= 0)
        if miss.any() and (b[:, k] > 0).sum() >= 5:
            b[miss, k] = b[b[:, k] > 0, k].mean()
    base_national = weights @ b / weights.sum()

    window, medians = poll_summary(target, cutoff, exclude_firms)
    national = base_national.copy()
    polled = np.zeros(K, bool)
    for f, m in medians.items():
        national[labels.index(f)] = m["median"] / 100
        polled[labels.index(f)] = True
    rest = national[~polled].sum()
    national[polled] *= (1 - rest) / national[polled].sum()

    ccaa_codes = sorted(set(CCAA.values()))
    ccaa = np.array([ccaa_codes.index(CCAA[c]) for c in CODES])
    return Setup(key=key, families=list(target.families), labels=labels, codes=list(CODES),
                 ccaa=ccaa, n_ccaa=len(ccaa_codes), seats=np.asarray(seats, int),
                 electors=np.asarray(electors, float), turnout=turnout,
                 valid_ratio=valid_ratio, base=b, present=present, weights=weights,
                 base_national=base_national, national=national, polled=polled,
                 cutoff=cutoff, lead=lead, window=window, poll_medians=medians,
                 actual_seats=actual_seats, actual_shares=actual_shares)


def _base_2026(b: np.ndarray, present: np.ndarray, base_sh: pd.DataFrame, labels: list[str],
               weights: np.ndarray) -> np.ndarray:
    """2026 lists without a 2023 list of their own.

    Sumar (2023) -> Frente Amplio and Podemos: where both run, by Podemos's share of the two in
    the 2024 European election; where only one runs, Frente Amplio takes all of Sumar and
    Podemos its European share (the rest is spread over the other lists). In the Canaries the
    Frente Amplio list includes Nueva Canarias, whose 2023 vote is added. SALF: its 2024
    European share. A list with no 2023 list in a constituency where it runs in 2026 (Vox in
    Santa Cruz de Tenerife): its 2024 European share there, scaled by its 2023/2024 national
    ratio."""
    ep = ep_shares()
    fa, pod, salf = (labels.index(x) for x in ("FA", "PODEMOS", "SALF"))
    sumar = base_sh.get("SUMAR", 0 * base_sh.iloc[:, 0]).to_numpy()
    nc = base_sh.get("NC", 0 * base_sh.iloc[:, 0]).to_numpy()
    r = (ep["PODEMOS"] / (ep["PODEMOS"] + ep["SUMAR"])).to_numpy()
    both = present[:, fa] & present[:, pod]
    b[:, fa] = np.where(both, sumar * (1 - r), np.where(present[:, fa], sumar, 0)) + nc
    b[:, pod] = np.where(present[:, pod], sumar * r, 0)
    b[:, salf] = ep["SALF"].to_numpy()
    for lab in ("PP", "PSOE", "VOX"):
        k = labels.index(lab)
        miss = present[:, k] & (b[:, k] <= 0)
        if miss.any():
            ok = b[:, k] > 0
            scale = (weights[ok] @ b[ok, k]) / (weights[ok] @ ep[lab].to_numpy()[ok])
            b[miss, k] = ep[lab].to_numpy()[miss] * scale
    return b


# --- calibration ----------------------------------------------------------------------------


@dataclass
class Calibration:
    before: str
    lead: int
    sigma_national: float
    tau_ccaa: float
    tau_province: float
    sigma_turnout_national: float
    sigma_turnout_province: float
    errors: pd.DataFrame
    n_residuals: int
    pairs: list[tuple[str, str]]
    within_bloc_check: dict

    def as_dict(self) -> dict:
        return {"before": self.before, "lead_days": self.lead,
                "sigma_national_logit": self.sigma_national,
                "tau_ccaa": self.tau_ccaa, "tau_province": self.tau_province,
                "sigma_turnout_national_logit": self.sigma_turnout_national,
                "sigma_turnout_province_logit": self.sigma_turnout_province,
                "n_poll_errors": len(self.errors), "n_provincial_residuals": self.n_residuals,
                "pairs": [list(p) for p in self.pairs],
                "within_bloc_check": self.within_bloc_check}


def poll_errors(elections: list[str], lead: int) -> pd.DataFrame:
    """Actual minus median (logit scale) for every poll column with at least MIN_FIRMS firms
    and an actual share of at least 1%."""
    pr = data()["poll_results"]
    rows = []
    for e in elections:
        ed = date.fromisoformat(ELECTION_DATE[e])
        window = polls.window(poll_wide(e), ed - timedelta(days=lead))
        for _, r in pr[pr["election"] == e].iterrows():
            col, actual = r["party"], r["share"]
            if col not in window or window[col].notna().sum() < MIN_FIRMS:
                continue
            if actual < 100 * MIN_SHARE:
                continue
            med = float(window[col].median())
            rows.append({"election": e, "party": col, "median": med, "actual": actual,
                         "firms": int(window[col].notna().sum()), "n_firms": len(window),
                         "error_pp": actual - med,
                         "error_logit": float(logit(actual / 100) - logit(med / 100))})
    return pd.DataFrame(rows)


# Parties grouped as the 2023 investitures group them, for the within-bloc correlation check
# only (Cs grouped by its vote for Rajoy's 2016 investiture).
CHECK_BLOCS = {"F": ("PP", "VOX", "CS"), "S": ("PSOE", "PODEMOS", "UP", "SUMAR", "MP", "IU")}


def _within_bloc(errors: pd.DataFrame, sigma: float) -> dict:
    """Method of moments: if errors were (bloc effect + own error), the squared mean error of
    a bloc's parties would exceed sigma²/n on average. Reports the estimate of the bloc
    variance (negative means no positive within-bloc correlation)."""
    rows = []
    for _, g in errors.assign(
            bloc=errors["party"].map({p: b for b, ps in CHECK_BLOCS.items() for p in ps})
    ).dropna(subset=["bloc"]).groupby(["election", "bloc"]):
        if len(g) >= 2:
            rows.append((g["error_logit"].mean() ** 2, 1 / len(g)))
    if not rows:
        return {"bloc_variance": None, "n": 0}
    ms, inv_n = np.array(rows).T
    var_b = float(ms.mean() - sigma ** 2 * inv_n.mean())
    return {"bloc_variance": var_b, "n": len(rows),
            "implied_within_bloc_correlation": max(var_b, 0) / sigma ** 2}


PAIR_MERGE = {("2015", "2016"): {"UP": ("UP", "IU")},
              ("2019N", "2023"): {"SUMAR": ("UP", "MP")}}


def provincial_residuals(pairs: list[tuple[str, str]]) -> pd.DataFrame:
    """log(share1/share0) - log(national1/national0) for every list in both elections with at
    least 1% in the constituency (both times) and nationally."""
    rows = []
    for e0, e1 in pairs:
        s0, s1 = shares(e0), shares(e1)
        v0, v1 = summary(e0)["valid"].to_numpy(), summary(e1)["valid"].to_numpy()
        merge = PAIR_MERGE.get((e0, e1), {})
        for lab in s1.columns:
            if lab in ("OTH", "BLANK"):
                continue
            a = s1[lab].to_numpy()
            src = merge.get(lab, (lab,))
            if not all(x in s0.columns for x in src):
                continue
            z = s0[list(src)].sum(axis=1).to_numpy()
            ok = (a >= MIN_SHARE) & (z >= MIN_SHARE)
            if ok.sum() < 2:
                continue
            nat0, nat1 = (v0[ok] @ z[ok]) / v0[ok].sum(), (v1[ok] @ a[ok]) / v1[ok].sum()
            if min(nat0, nat1) < MIN_SHARE:
                continue
            r = np.log(a[ok] / z[ok]) - np.log(nat1 / nat0)
            for code, x in zip(np.array(CODES)[ok], r, strict=True):
                rows.append({"pair": f"{e0}->{e1}", "label": lab, "code": code,
                             "ccaa": CCAA[code], "r": float(x)})
    return pd.DataFrame(rows)


def _variance_components(res: pd.DataFrame) -> tuple[float, float]:
    """CCAA and constituency standard deviations of the residuals (one-way random effects
    within each pair and list, method of moments)."""
    res = res.copy()
    res["r"] -= res.groupby(["pair", "label"])["r"].transform("mean")
    g = res.groupby(["pair", "label", "ccaa"])["r"]
    dev = res["r"] - g.transform("mean")
    n_c = g.transform("size")
    dof = (g.size() - 1).clip(lower=0).sum()
    tau_e2 = float((dev ** 2).sum() / dof)
    means = g.mean()
    sizes = g.size()
    tau_c2 = float((means ** 2).mean() - tau_e2 * (1 / sizes).mean())
    del n_c
    return float(np.sqrt(max(tau_c2, 0.0))), float(np.sqrt(tau_e2))


def turnout_sigmas(pairs: list[tuple[str, str]]) -> tuple[float, float]:
    nat, prov = [], []
    for e0, e1 in pairs:
        a, b = summary(e0), summary(e1)
        t0 = logit(a["voters"] / a["electors"])
        t1 = logit(b["voters"] / b["electors"])
        T0 = logit(a["voters"].sum() / a["electors"].sum())
        T1 = logit(b["voters"].sum() / b["electors"].sum())
        nat.append(T1 - T0)
        prov += list((t1 - t0) - (T1 - T0))
    return float(np.sqrt(np.mean(np.square(nat)))), float(np.sqrt(np.mean(np.square(prov))))


def calibrate(before: str, lead: int) -> Calibration:
    """Everything estimated from the elections before `before` only."""
    past = [e for e in ELECTIONS if ELECTION_DATE[e] < ELECTION_DATE[before]]
    pairs = list(zip(past, past[1:], strict=False))
    errors = poll_errors(past, lead)
    sigma = float(np.sqrt(np.mean(np.square(errors["error_logit"]))))
    res = provincial_residuals(pairs)
    tau_c, tau_e = _variance_components(res)
    s_tn, s_tp = turnout_sigmas(pairs)
    return Calibration(before=before, lead=lead, sigma_national=sigma, tau_ccaa=tau_c,
                       tau_province=tau_e, sigma_turnout_national=s_tn,
                       sigma_turnout_province=s_tp, errors=errors, n_residuals=len(res),
                       pairs=pairs, within_bloc_check=_within_bloc(errors, sigma))


# --- simulation -----------------------------------------------------------------------------


@dataclass
class SimResult:
    n: int
    seats: np.ndarray        # (n, F) national seats per list
    blocs: np.ndarray        # (n, B) seats per bloc
    bloc_names: list[str]
    prov_seats: np.ndarray   # (I, F) mean seats
    prov_win: np.ndarray     # (I, F) P(at least one seat)
    votes: np.ndarray        # (I, K) mean votes
    quota: np.ndarray        # (I,) expected valid votes / seats
    h: np.ndarray            # (I, H) bandwidths in votes
    flips: np.ndarray | None = None   # (I, F, H) counts of 0 < Δ ≤ h
    pivots: np.ndarray | None = None  # (I, F, H, B+1) the same, and the seat changes a bloc's
    #                                    majority status; last index: any of the first two


def simulate(setup: Setup, calib: Calibration, n: int = 100_000, seed: int = SEED,
             widen: float = 1.0, chunk: int = 5_000, track: bool = True,
             blocs: dict[str, tuple[str, ...]] | None = None) -> SimResult:
    rng = np.random.default_rng(seed)
    blocs = blocs if blocs is not None else BLOCS[setup.key]
    NI, K, F = len(setup.codes), len(setup.labels), setup.F  # noqa: N806
    H = len(H_MULTS)
    bm = np.array([[lab in members for lab in setup.labels] for members in blocs.values()],
                  dtype=np.int16)  # (B, K)
    nb = len(blocs)
    capable = np.array([lab not in NONSEAT for lab in setup.labels])
    S, B0, polled = setup.national, setup.base_national, setup.polled
    rest = S[~polled].sum()
    quota = setup.weights / setup.seats
    h = quota[:, None] * np.array(H_MULTS)[None, :]
    sig = {k: v * widen for k, v in dict(
        nat=calib.sigma_national, tc=calib.tau_ccaa, te=calib.tau_province,
        tn=calib.sigma_turnout_national, tp=calib.sigma_turnout_province).items()}

    seats_all, blocs_all = [], []
    prov_seats = np.zeros((NI, K))
    prov_win = np.zeros((NI, K))
    votes_sum = np.zeros((NI, K))
    flips = np.zeros((NI, F, H)) if track else None
    pivots = np.zeros((NI, F, H, nb + 1)) if track else None
    base = setup.base[None]
    ratio_den = np.where(B0 > 0, B0, 1.0)
    for start in range(0, n, chunk):
        m = min(chunk, n - start)
        Sn = np.repeat(S[None], m, axis=0)
        eps = rng.standard_normal((m, int(polled.sum()))) * sig["nat"]
        Sn[:, polled] = expit(logit(S[polled])[None] + eps)
        Sn[:, polled] *= (1 - rest) / Sn[:, polled].sum(axis=1, keepdims=True)
        eta = rng.standard_normal((m, 1)) * sig["tn"]
        zeta = rng.standard_normal((m, NI)) * sig["tp"]
        V = setup.electors * expit(logit(setup.turnout) + eta + zeta) * setup.valid_ratio
        delta = (rng.standard_normal((m, setup.n_ccaa, K)) * sig["tc"])[:, setup.ccaa, :] + \
            rng.standard_normal((m, NI, K)) * sig["te"]
        s = base * (Sn / ratio_den)[:, None, :] * np.exp(delta)
        s /= s.sum(axis=2, keepdims=True)
        Vsum = V.sum(axis=1, keepdims=True)
        for _ in range(RAKE_ITERS):
            nat = np.einsum("mi,mik->mk", V, s) / Vsum
            s *= np.where(nat > 0, Sn / np.maximum(nat, 1e-15), 1.0)[:, None, :]
            s /= s.sum(axis=2, keepdims=True)
        v = s * V[:, :, None]
        seats = np.zeros((m, NI, K), dtype=np.int16)
        for i in range(NI):
            elig = capable[None] & setup.present[i][None] & (v[:, i] >= dhondt.THRESHOLD *
                                                              V[:, i:i + 1])
            seats[:, i] = dhondt.allocate(v[:, i], int(setup.seats[i]), elig)
        nat_seats = seats.sum(axis=1)
        btot = nat_seats.astype(np.int32) @ bm.T  # (m, B)
        status = btot >= parties.MAJORITY
        seats_all.append(nat_seats[:, :F].copy())
        blocs_all.append(btot)
        prov_seats += seats.sum(axis=0)
        prov_win += (seats > 0).sum(axis=0)
        votes_sum += v.sum(axis=0)
        if not track:
            continue
        pres_cap = setup.present & capable[None]
        for i in range(NI):
            need, loser = dhondt.margins(v[:, i], seats[:, i], pres_cap[i][None], V[:, i])
            within = (need[..., None] > 0) & (need[..., None] <= h[i][None, None, :])  # m,K,H
            flips[i] += within[:, :F].sum(axis=0)
            d_b = bm[:, None, :] - bm[:, loser]                      # (B, m, K)
            new = (btot.T[:, :, None] + d_b) >= parties.MAJORITY
            change = new != status.T[:, :, None]                     # (B, m, K)
            any_change = change[: min(2, nb)].any(axis=0)
            for b_ in range(nb):
                pivots[i, :, :, b_] += (within & change[b_][..., None])[:, :F].sum(axis=0)
            pivots[i, :, :, nb] += (within & any_change[..., None])[:, :F].sum(axis=0)
    return SimResult(n=n, seats=np.concatenate(seats_all), blocs=np.concatenate(blocs_all),
                     bloc_names=list(blocs), prov_seats=prov_seats[:, :F] / n,
                     prov_win=prov_win[:, :F] / n, votes=votes_sum / n, quota=quota, h=h,
                     flips=flips, pivots=pivots)
