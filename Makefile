# The pipeline, one target per step: `make all` refreshes the polls and rebuilds everything.
# Each target is one `voteev` command (see `uv run voteev --help`).

RUN := uv run voteev

.PHONY: all data download prepare analyze simulate backtest outputs figures carousel tables check test lint

all: data analyze outputs check

data: download prepare

download:
	$(RUN) download

prepare:
	$(RUN) prepare

analyze:
	$(RUN) analyze

simulate:
	$(RUN) simulate

backtest:
	$(RUN) backtest

outputs: figures carousel tables

figures:
	$(RUN) figures

carousel:
	$(RUN) carousel

tables:
	$(RUN) tables

check:
	$(RUN) check

test:
	uv run pytest

lint:
	uv run ruff check src tests
