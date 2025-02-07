alias s := setup
alias i := install
alias t := test
alias tc := test-cov
alias r := run
alias rp := run_profiling
alias c := check
alias f := fmt
alias l := lint

setup:
    uv venv {{ justfile_directory() }}/.venv
    . {{ justfile_directory() }}/.venv/bin/activate
    just install
    pre-commit install --install-hooks

install:
    uv sync --all-extras

test:
    pytest -vv

test-cov:
    pytest --cov={{ justfile_directory() }}/yak_server \
      --cov={{ justfile_directory() }}/scripts \
      --cov={{ justfile_directory() }}/tests \
      --cov={{ justfile_directory() }}/testing \
      --cov-report=html \
      --cov-config={{ justfile_directory() }}/pyproject.toml \
      -vv

run:
    uvicorn --reload --factory yak_server:create_app

run_profiling:
    uvicorn --reload --factory scripts.profiling:create_app

check:
    pre-commit run -a

fmt:
    pre-commit run -a ruff-format

lint:
    pre-commit run -a ruff
