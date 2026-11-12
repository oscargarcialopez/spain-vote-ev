"""voteev: the pipeline, one step per command.

    voteev download    fetch the sources into data/raw/ (polls are refetched every time)
    voteev prepare     parse them into data/processed/
    voteev simulate    a quick 2026 run: seats, blocs and pivot odds, nothing written
    voteev backtest    the pre-declared backtests (Nov 2019, 2023) and their coverage
    voteev analyze     everything: writes results/summary.json, the only source of numbers
    voteev figures     the four figures, as PNG (and SVG) in figures/
    voteev carousel    the nine-page carousel: carousel/carousel.pdf, slide-NN.png, slides.txt
    voteev tables      rewrite the README's generated tables from summary.json
    voteev check       flag numbers in the published texts that are not in results/summary.json,
                       or not written in their language's format
"""

from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path

from .sources import RESULTS, ROOT

# The published texts and their language; a file can switch midway with a line
# `<!-- lang: en -->` (see facts.py).
CHECKED = [("README.md", "en"), ("POST.md", "en"), ("carousel/slides.txt", "en")]


def _download(a: argparse.Namespace) -> int:
    from . import download
    if a.verify:
        bad = download.verify()
        print("manifest ok" if not bad else "changed or missing: " + ", ".join(bad))
        return 1 if bad else 0
    download.download(only=a.only, refresh_polls=not a.keep_polls, force=a.force)
    return 0


def _prepare(a: argparse.Namespace) -> int:
    from . import prepare
    prepare.prepare()
    return 0


def _simulate(a: argparse.Namespace) -> int:
    from . import analysis, model
    setup = model.build("2026", cutoff=a.cutoff)
    calib = model.calibrate("2026", setup.lead)
    print(f"cutoff {setup.cutoff}, {len(setup.window)} firms, lead {setup.lead} days, "
          f"n = {a.n:,}")
    sim = model.simulate(setup, calib, n=a.n, widen=a.widen, track=True)
    for v in analysis.seat_table(setup, sim).values():
        print(f"  {v['name']:20s} {v['mean']:6.1f}  80%: {v['lo80']:3d}-{v['hi80']:<3d}"
              f"  95%: {v['lo95']:3d}-{v['hi95']:<3d}")
    for b, v in analysis.bloc_table(setup, sim).items():
        print(f"  bloc {b:12s} {v['mean']:6.1f}  P(>= 176) = {v['p_majority']:.3f}")
    for ev, v in analysis.vote_probabilities(setup, sim)["national"].items():
        print(f"  {ev:22s} 1 in {v['one_in']:,.0f}")
    return 0


def _backtest(a: argparse.Namespace) -> int:
    from . import backtest
    bt = backtest.run(lead=a.lead, n=a.n)
    for t in bt["tried"]:
        print(f"factor {t['factor']}: 80% {t['in80']}/{t['lists']} ({t['cov80']:.0%}), "
              f"95% {t['in95']}/{t['lists']} ({t['cov95']:.0%})")
        for run in t["runs"]:
            for x in run["lists"]:
                if x["counted"]:
                    mark = "" if x["in80"] else ("  outside 80%" if x["in95"] else
                                                 "  outside 95%")
                    print(f"  {run['election']:6s} {x['list']:8s} actual {x['actual']:3d}  "
                          f"80%: {x['lo80']}-{x['hi80']}  95%: {x['lo95']}-{x['hi95']}{mark}")
    print(f"chosen factor: {bt['chosen_factor']}")
    return 0


def _analyze(a: argparse.Namespace) -> int:
    from . import analysis
    analysis.run(n=a.n, cutoff=a.cutoff, backtest_n=a.backtest_n)
    return 0


def _figures(a: argparse.Namespace) -> int:
    from . import carousel
    carousel.make_figures(RESULTS, ROOT / "figures")
    return 0


def _carousel(a: argparse.Namespace) -> int:
    from . import carousel
    carousel.make_carousel(RESULTS, ROOT / "carousel", ROOT / "figures")
    return 0


def _tables(a: argparse.Namespace) -> int:
    from . import style, tables
    done = tables.update(ROOT / "README.md", style.load_summary(RESULTS))
    print("README.md tables: " + (", ".join(done) or "no markers found"))
    return 0


def _check(a: argparse.Namespace) -> int:
    from . import facts, style
    pairs = ([(Path(p), a.lang) for p in a.files] if a.files
             else [(ROOT / p, lang) for p, lang in CHECKED])
    missing = [p for p, _ in pairs if not p.exists()]
    for p in missing:
        print(f"{p}: missing")
    bad = facts.check_files([(p, lang) for p, lang in pairs if p.exists()],
                            style.load_summary(RESULTS))
    return 1 if bad or missing else 0


def main(argv: list[str] | None = None) -> int:
    from . import backtest
    from .analysis import N
    ap = argparse.ArgumentParser(prog="voteev", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("download", help="fetch the sources into data/raw/")
    p.add_argument("--only", nargs="*", help="files whose name contains any of these")
    p.add_argument("--keep-polls", action="store_true", help="do not refetch the poll pages")
    p.add_argument("--force", action="store_true", help="refetch everything")
    p.add_argument("--verify", action="store_true", help="only check the SHA-256 manifest")
    p.set_defaults(fn=_download)
    sub.add_parser("prepare", help="parse data/raw/ into data/processed/").set_defaults(
        fn=_prepare)
    p = sub.add_parser("simulate", help="a quick 2026 run, nothing written")
    p.add_argument("--n", type=int, default=20_000)
    p.add_argument("--cutoff", type=date.fromisoformat, default=None)
    p.add_argument("--widen", type=float, default=1.0)
    p.set_defaults(fn=_simulate)
    p = sub.add_parser("backtest", help="the pre-declared backtests")
    p.add_argument("--n", type=int, default=backtest.N)
    p.add_argument("--lead", type=int, default=backtest.LEAD)
    p.set_defaults(fn=_backtest)
    p = sub.add_parser("analyze", help="write results/summary.json")
    p.add_argument("--n", type=int, default=N)
    p.add_argument("--backtest-n", type=int, default=backtest.N)
    p.add_argument("--cutoff", type=date.fromisoformat, default=None,
                   help="last fieldwork day of the polls (default: the latest poll)")
    p.set_defaults(fn=_analyze)
    sub.add_parser("figures", help="figures/*.png from summary.json").set_defaults(
        fn=_figures)
    sub.add_parser("carousel", help="the carousel from summary.json").set_defaults(
        fn=_carousel)
    sub.add_parser("tables", help="rewrite the README's generated tables").set_defaults(
        fn=_tables)
    p = sub.add_parser("check", help="numbers in the texts that are not in summary.json")
    p.add_argument("files", nargs="*", help="default: the published texts, each in its language")
    p.add_argument("--lang", choices=["en", "es"], default="en",
                   help="language of the files given (default en)")
    p.set_defaults(fn=_check)
    a = ap.parse_args(argv)
    return a.fn(a)


if __name__ == "__main__":
    sys.exit(main())
