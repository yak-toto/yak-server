alias s := setup
alias i := install
alias t := test
alias tc := test-cov
alias r := run
alias rp := run_profiling
alias c := check
alias f := fmt
alias l := lint
alias ud := update_deps
alias bi := build_image

setup:
    just install
    uv run prek install --install-hooks

install:
    uv sync --all-groups

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

run:
    uv run uvicorn --reload --factory yak_server:create_app

run_profiling:
    uv run uvicorn --reload --factory scripts.profiling:create_app

check:
    uv run prek run -a

fmt:
    uv run prek run -a ruff-format

lint:
    uv run prek run -a ruff-check

update_deps:
    uv run prek autoupdate
    uv lock -U

build_image COMPETITION:
    {{ justfile_directory() }}/scripts/build_image.sh {{COMPETITION}}
