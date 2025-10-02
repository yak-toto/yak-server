# Yak-toto

[![PyPI](https://img.shields.io/pypi/v/yak-server?label=stable)](https://pypi.org/project/yak-server/)
[![Python Versions](https://img.shields.io/pypi/pyversions/yak-server)](https://pypi.org/project/yak-server/)
[![codecov](https://codecov.io/gh/yak-toto/yak-server/branch/main/graph/badge.svg?token=EZZK5SY5BL)](https://codecov.io/gh/yak-toto/yak-server)
[![🔐 CodeQL](https://github.com/yak-toto/yak-server/actions/workflows/codeql-analysis.yml/badge.svg)](https://github.com/yak-toto/yak-server/actions/workflows/codeql-analysis.yml)
[![Testing](https://github.com/yak-toto/yak-server/actions/workflows/test.yml/badge.svg)](https://github.com/yak-toto/yak-server/actions/workflows/test.yml)

## Recommended tooling

- [`uv`](https://github.com/astral-sh/uv): a modern Python dependency manager
- [`docker`](https://docs.docker.com/get-docker/) or [`podman`](https://podman.io/getting-started/installation) to start a Postgres database

## How to build the project

### Database

To setup a database, run `yak env init`. This will ask you to fill different configuration in order build env file.
Once done, you can run the Docker script at `scripts/postgresrun.sh` to start the Postgres database.

### Backend

Running your project in a Python virtual environment is highly recommended.

You can use venv python module using the following command:

```bash
uv venv
source .venv/bin/activate
```

Fetch all packages using uv with the following command:

```bash
uv sync
```

Before starting the backend, add `JWT_SECRET_KEY` and `JWT_EXPIRATION_TIME` to your `.env` file, along with the Postgres user name and password.
Since the login system uses JSON Web Token, a secret key is required and an expiration time (in seconds). To generate one, you can use the python built-in `secrets` module.

```py
>>> import secrets
>>> secrets.token_hex(16)
'9292f79e10ed7ed03ffad66d196217c4'
```

```text
JWT_SECRET_KEY=9292f79e10ed7ed03ffad66d196217c4
JWT_EXPIRATION_TIME=1800
```

Automatic backups can be performed using the `yak_server/cli/backup_database` script. It can be run using `yak db backup`.

Finally, fastapi needs some configuration to start. For the development environment, debugging needs to be activated with an additional environment variable:

```text
DEBUG=1
```

And then start backend with:

```bash
uvicorn --reload yak_server:create_app --factory
```

### Data initialization

To run local testing, you can use the script `create_database.py`, `initialize_database.py` and `create_admin.py` located in the `yak_server/cli` folder. To select the competition, set the `COMPETITION` environment variable in `.env`. It will read data from `yak_server/data/{COMPETITION}/`.

### Testing

Yak-server is using `pytest` to run tests.

## Profiling

You can run the application with profiler attached. To do so, please run the following command

```bash
uvicorn --reload scripts.profiling:create_app --factory
```
