# Yak-toto

## Requisites

- Ubuntu 22.04
- Python 3.10.4
- MySQL 8.0.30

## How to build the project

### Database

Install and start mysql server on port 3306. Add a database named `yak_toto`. In root folder, create a dotenv file named `.flaskenv` and fill your MySQL user name and password. When backend start, this configuration is automaticaly loaded.

```text
MYSQL_USER_NAME=my_user_name
MYSQL_PASSWORD=my_password
```

### Backend

Run your project in a Python env is highly recommend. You can use `venv` with the following command:

```bash
python3 -m venv <my_env_name>
```

Then activate it with:

```bash
source <my_env_name>/bin/activate
```

Fetch all packages using setuptools with the following command:

```bash
python setup.py install
```

Before starting the backend, add `JWT_SECRET_KEY` in `.flaskenv` same as the MySQL user name and password. As
login system is using JSON Web Token, a secret key is required. To generate one, you can use the python built-in `secrets` module.

```py
>>> import secrets
>>> secrets.token_hex(16)
'9292f79e10ed7ed03ffad66d196217c4'
```

```text
JWT_SECRET_KEY=9292f79e10ed7ed03ffad66d196217c4
```

Also, the backend is able send logs to a Telegram bot. To do so, please add a bot token and chat id to `.flaskenv`.

```text
BOT_TOKEN=my_bot_token
CHAT_ID=my_chat_id
```

Finally, flask needs some configuration to start. Please add `FLASK_APP=server` variable to indicate main location. Last thing, for development environment, debug needs to be activated with a addditional environment variable:

```text
FLASK_DEBUG=1
```

And then start backend with:

```bash
flask run
```
