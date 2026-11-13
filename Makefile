# The pipeline, one target per step: `make all` refreshes the polls and rebuilds everything,
# as `uv run voteev all` does without make. Each target is one `voteev` command (see
# `uv run voteev --help`). CUTOFF=YYYY-MM-DD sets the last fieldwork day of the polls
# (default: the latest poll), e.g. to see how the texts read with other numbers:
# `make analyze outputs check CUTOFF=2026-11-05`.

RUN := uv run voteev
CUTOFF ?=

.PHONY: all data download prepare analyze simulate backtest outputs figures carousel texts check test lint

all: data analyze outputs check

data: download prepare

download:
	$(RUN) download

prepare:
	$(RUN) prepare

analyze:
	$(RUN) analyze $(if $(CUTOFF),--cutoff $(CUTOFF))

simulate:
	$(RUN) simulate

backtest:
	$(RUN) backtest

outputs: figures carousel texts

figures:
	$(RUN) figures

carousel:
	$(RUN) carousel --lang es
	$(RUN) carousel --lang en

texts:
	$(RUN) texts

check:
	$(RUN) check

test:
	uv run pytest

lint:
	uv run ruff check src tests
