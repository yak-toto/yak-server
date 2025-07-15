# Yak-toto

[![PyPI](https://img.shields.io/pypi/v/yak-server?label=stable)](https://pypi.org/project/yak-server/)
[![Python Versions](https://img.shields.io/pypi/pyversions/yak-server)](https://pypi.org/project/yak-server/)
[![codecov](https://codecov.io/gh/yak-toto/yak-server/branch/main/graph/badge.svg?token=EZZK5SY5BL)](https://codecov.io/gh/yak-toto/yak-server)
[![🔐 CodeQL](https://github.com/yak-toto/yak-server/actions/workflows/codeql-analysis.yml/badge.svg)](https://github.com/yak-toto/yak-server/actions/workflows/codeql-analysis.yml)
[![Testing](https://github.com/yak-toto/yak-server/actions/workflows/test.yml/badge.svg)](https://github.com/yak-toto/yak-server/actions/workflows/test.yml)

## Requisites

- Ubuntu 22.04
- Postgres 17.2

## How to build the project

### Database

To setup a database, run `yak env init`. This will ask you to fill different configuration in order build env file.
Once done, you can run a docker script to start postgres database (at `scripts/postgresrun.sh`)

### Backend

Run your project in a Python env is highly recommend. You can use venv python module using the following command:

```bash
uv venv
. .venv/bin/activate
```

Fetch all packages using uv with the following command:

```bash
uv pip install -e .
```

Before starting the backend, add `JWT_SECRET_KEY` and `JWT_EXPIRATION_TIME` in `.env` same as the Postgres user name and password. As
login system is using JSON Web Token, a secret key is required and an expiration time (in seconds). To generate one, you can use the python built-in `secrets` module.

```py
>>> import secrets
>>> secrets.token_hex(16)
'9292f79e10ed7ed03ffad66d196217c4'
```

```text
JWT_SECRET_KEY=9292f79e10ed7ed03ffad66d196217c4
JWT_EXPIRATION_TIME=1800
```

Also, automatic backup can be done through `yak_server/cli/backup_database` script. It can be run using `yak db backup`.

Finally, fastapi needs some configuration to start. Last thing, for development environment, debug needs to be activated with a additional environment variable:

```text
DEBUG=1
```

And then start backend with:

```bash
uvicorn --reload yak_server:create_app --factory
```

### Data initialization

To run local testing, you can use the script `create_database.py`, `initialize_database.py` and `create_admin.py` located in `yak_server/cli` folder. To select, set `COMPETITION` environment variable in `.env`. It will read data from `yak_server/data/{COMPETITION}/`.

### Testing

Yak-server is using `pytest` to run tests.

## Profiling

You can run the application with profiler attached. To do so, please run the following command

```bash
uvicorn --reload scripts.profiling:create_app --factory
```
