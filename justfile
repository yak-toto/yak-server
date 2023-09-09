alias s := setup
alias i := install
alias t := test
alias tc := test-cov
alias tcs := test-cov-slipcover
alias r := run
alias c := check
alias f := fmt
alias l := lint

setup:
    uv venv {{ justfile_directory() }}/.venv
    . {{ justfile_directory() }}/.venv/bin/activate
    just install
    pre-commit install --install-hooks

install:
    uv pip install -r {{ justfile_directory() }}/requirements.txt

test:
    pytest -vv

test-cov:
    pytest --cov={{ justfile_directory() }}/yak_server \
      --cov={{ justfile_directory() }}/scripts \
      --cov={{ justfile_directory() }}/tests \
      --cov={{ justfile_directory() }}/testing \
      --cov-report=xml \
      --cov-config={{ justfile_directory() }}/pyproject.toml \
      -vv

test-cov-slipcover:
    slipcover --branch --source yak_server,scripts,tests --out coverage.json --json -m pytest -vv

run:
    uvicorn --reload --factory yak_server:create_app

check:
    pre-commit run -a

fmt:
    pre-commit run -a ruff-format

lint:
    pre-commit run -a ruff
