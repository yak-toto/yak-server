alias s := setup
alias i := install
alias t := test
alias tc := test-cov
alias tcs := test-cov-slipcover
alias r := run
alias rp := run_profiling
alias c := check
alias f := fmt
alias l := lint
alias ud := update_deps

setup:
    just install
    uv run pre-commit install --install-hooks

install:
    uv sync --all-extras --all-groups

test:
    uv run pytest -vv

test-cov:
    uv run pytest --cov={{ justfile_directory() }}/yak_server \
      --cov={{ justfile_directory() }}/scripts \
      --cov={{ justfile_directory() }}/tests \
      --cov={{ justfile_directory() }}/testing \
      --cov-report=html \
      --cov-config={{ justfile_directory() }}/pyproject.toml \
      -vv

tox:
    {{ justfile_directory() }}/tox.sh

test-cov-slipcover:
    uv run slipcover --branch --source yak_server,scripts,tests,testing --out coverage.json --json -m pytest -vv

run:
    uv run uvicorn --reload --factory yak_server:create_app

run_profiling:
    uv run uvicorn --reload --factory scripts.profiling:create_app

check:
    uv run pre-commit run -a

fmt:
    uv run pre-commit run -a ruff-format

lint:
    uv run pre-commit run -a ruff-check

update_deps:
    uv run pre-commit autoupdate
    uv lock -U
