# Yak-toto

[![PyPI](https://img.shields.io/pypi/v/yak-server?label=stable)](https://pypi.org/project/yak-server/)
[![Python Versions](https://img.shields.io/pypi/pyversions/yak-server)](https://pypi.org/project/yak-server/)
[![codecov](https://codecov.io/gh/yak-toto/yak-server/branch/main/graph/badge.svg?token=EZZK5SY5BL)](https://codecov.io/gh/yak-toto/yak-server)
[![🔐 CodeQL](https://github.com/yak-toto/yak-server/actions/workflows/codeql-analysis.yml/badge.svg)](https://github.com/yak-toto/yak-server/actions/workflows/codeql-analysis.yml)
[![Testing](https://github.com/yak-toto/yak-server/actions/workflows/test.yml/badge.svg)](https://github.com/yak-toto/yak-server/actions/workflows/test.yml)

## Requisites

- Ubuntu 22.04
- MySQL 8.0.30

## How to build the project

### Database

Install and start mysql server on port 3306. Add a database named `yak_toto`. In root folder, create a dotenv file named `.env` and fill your MySQL user name, password and database. When backend start, this configuration is automaticaly loaded.

```text
MYSQL_USER_NAME=my_user_name
MYSQL_PASSWORD=my_password
MYSQL_DB=my_database_name
```

You can also set MySQL port by adding `MYSQL_PORT=my_port` to `.env` file. If not set, it will be 3306 by default.

### Backend

Run your project in a Python env is highly recommend. You can use venv python module using the following command:

```bash
python -m venv venv
. venv/bin/activate
```

Fetch all packages using pip with the following command:

```bash
pip install -r requirements.txt
```

Before starting the backend, add `JWT_SECRET_KEY` and `JWT_EXPIRATION_TIME` in `.env` same as the MySQL user name and password. As
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

Finally, fastapi needs some configuration to start. Last thing, for development environment, debug needs to be activated with a addditional environment variable:

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

To set up test, please add a MySQL database named `yak_toto_test`. It will contain all the records created during unit tests. This database is cleaned everytime you run test. That's why a different database is created to avoid deleting records you use for your local testing.

Yak-server is using `pytest` to run tests.

## Profiling

You can profile by adding this line in the `.env`

```text
PROFILING=1
```

Be careful, you need to be in debug mode to activate the profiling. In production mode, adding the environment variable will have no impacts.
