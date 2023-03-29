# Yak-toto

[![PyPI](https://img.shields.io/pypi/v/yak-server?label=stable)](https://pypi.org/project/yak-server/)
[![Python Versions](https://img.shields.io/pypi/pyversions/yak-server)](https://pypi.org/project/yak-server/)
[![codecov](https://codecov.io/gh/yak-toto/yak-server/branch/master/graph/badge.svg?token=EZZK5SY5BL)](https://codecov.io/gh/yak-toto/yak-server)
[![🔐 CodeQL](https://github.com/yak-toto/yak-server/actions/workflows/codeql-analysis.yml/badge.svg)](https://github.com/yak-toto/yak-server/actions/workflows/codeql-analysis.yml)

## Requisites

- Ubuntu 22.04
- MySQL 8.0.30

## How to build the project

### Database

Install and start mysql server on port 3306. Add a database named `yak_toto`. In root folder, create a dotenv file named `.flaskenv` and fill your MySQL user name, password and database. When backend start, this configuration is automaticaly loaded.

```text
MYSQL_USER_NAME=my_user_name
MYSQL_PASSWORD=my_password
MYSQL_DB=my_database_name
```

You can also set MySQL port by adding `MYSQL_PORT=my_port` to `.flaskenv` file. If not set, it will be 3306 by default.

### Backend

Run your project in a Python env is highly recommend. You can use `venv` with the following command:

```bash
python3 -m venv <my_env_name>
```

Then activate it with:

```bash
source <my_env_name>/bin/activate
```

Fetch all packages using poetry with the following command:

```bash
poetry install
```

Before starting the backend, add `JWT_SECRET_KEY` and `JWT_EXPIRATION_TIME` in `.flaskenv` same as the MySQL user name and password. As
login system is using JSON Web Token, a secret key is required and an expiration time (in seconds). To generate one, you can use the python built-in `secrets` module.

```py
>>> import secrets
>>> secrets.token_hex(16)
'9292f79e10ed7ed03ffad66d196217c4'
```

```text
JWT_SECRET_KEY=9292f79e10ed7ed03ffad66d196217c4
```

Also, automatic backup can be done through `yak_server/cli/backup_database` script. It can be run using `flask db backup`.

Finally, flask needs some configuration to start. Please add `FLASK_APP=yak_server` variable to indicate main location. Last thing, for development environment, debug needs to be activated with a addditional environment variable:

```text
FLASK_DEBUG=1
```

And then start backend with:

```bash
flask run
```

### Data initialization

To run local testing, you can use the script `create_database.py`, `initialize_database.py` and `create_admin.py` located in `yak_server/cli` folder. To select, set `COMPETITION` environment variable in `.flaskenv`. It will read data from `yak_server/data/{COMPETITION}/`.

### Testing

To set up test, please add a MySQL database named `yak_toto_test`. It will contain all the records created during unit tests. This database is cleaned everytime you run test. That's why a different database is created to avoid deleting records you use for your local testing.

Yak-server is using `pytest` to run tests and can run them using `poetry run pytest` command into root folder.
