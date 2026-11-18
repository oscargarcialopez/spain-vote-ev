# AGENTS.md

## What this is

A seat simulation of Spain's general election of 29 November 2026, built to estimate how likely
one more vote is to change a seat or who is invested prime minister. The package `spain_vote_ev`
and its CLI, `voteev`, run the pipeline from public sources to the published texts and carousels.
The question, method, data and limits are in [README.md](README.md).

## Layout

- `src/spain_vote_ev/`: the package; `cli.py` defines every `voteev` command.
- `src/spain_vote_ev/templates/`: the templates of `README.md` and `POST.md`.
- `src/spain_vote_ev/fonts/`: STIX Two, vendored for the figures and the carousels.
- `data/raw/`: the downloads, not committed except `MANIFEST.tsv` (their SHA-256 manifest).
- `data/processed/`: the parsed inputs of the model, committed.
- `data/curated/`: records transcribed by hand, each with its source.
- `results/summary.json`: every published number. `results/*.csv`: per-province tables.
- `figures/`, `carousel/` (Spanish, the one posted) and `carousel/en/`: generated outputs.
- `README.md` and `POST.md` (the LinkedIn post): generated from the templates.
- `tests/`: pytest on the committed data; no network needed.

## Commands

There is no install target: run `uv sync`. The pipeline targets wrap `voteev` commands
(`uv run voteev --help`).

- `make all`: data, analyze, outputs and check, in that order; refetches the polls.
- `make data`: download and prepare.
- `make download`: fetch the sources into `data/raw/` (network; refetches the polls every time).
- `make prepare`: parse `data/raw/` into `data/processed/`.
- `make analyze`: backtests and simulation into `results/`; `CUTOFF=YYYY-MM-DD` drops later polls.
- `make simulate`: a quick 2026 run that prints seats and odds and writes nothing.
- `make backtest`: the pre-declared backtests and their coverage, printed.
- `make outputs`: figures, carousel and texts.
- `make figures`: the figures in `figures/`, from `results/summary.json`.
- `make carousel`: the Spanish carousel in `carousel/`, the English one in `carousel/en/`.
- `make texts`: `README.md` and `POST.md` from their templates and `results/summary.json`.
- `make check`: the numbers in the texts against `results/summary.json`; the carousels' layout.
- `make test`: pytest. One test: `uv run pytest tests/test_dhondt.py::test_textbook_example -q`.
- `make lint`: ruff on `src` and `tests`.

## Rules

- No paid API: the pipeline calls none, and adding one needs the owner's explicit OK, with every
  response cached so a rerun costs nothing. Only `voteev download` (`make all`, `make data`,
  `make download`) touches the network: it refetches the Wikipedia poll pages, which moves every
  number, so it never runs without the owner's OK.
- Every number in `README.md`, `POST.md` and the carousels comes from `results/summary.json`, and
  `voteev check` verifies it, in each language's format. Change the data or the model and
  regenerate; never edit a number in the prose. A post kept outside the repo is checked the same
  way: `uv run voteev check --lang es FILE`.
- `README.md` and `POST.md` are written by `make texts`: edit the templates, never these files.
- The carousels and `figures/` are generated: never edit them by hand.
- Never commit secrets, `.env` or `*:Zone.Identifier` files. Stage files by name, not with
  `git add -A`.
- Write everything in English: code, comments, docs, commits. Spanish appears only in what is
  published in Spanish (the post, the Spanish carousel) and in parsing Spanish sources.

## Definition of done

These pass, as they do in CI (`.github/workflows/ci.yml`):

```bash
uv sync --locked
make check
make lint
make test
```

If a change can move a published number or word, regenerate before the checks (`make texts`
after a template, `make outputs` after the code that writes the outputs, `make analyze outputs`
after the data or the model) and commit the regenerated files with it.

## Commits

Conventional Commits, with a header of at most 60 characters, e.g.
`fix(carousel): unbroken dates, sigma, takeaway`.
