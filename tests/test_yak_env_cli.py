import json
from pathlib import Path
from secrets import randbelow

from dotenv import dotenv_values
from typer.testing import CliRunner

from yak_server.cli import app

from .utils import get_random_string

runner = CliRunner()


def test_yak_env_init() -> None:
    user_name = get_random_string(15)
    password = get_random_string(250)
    port = randbelow(80000)
    database = get_random_string(15)

    with runner.isolated_filesystem():
        result = runner.invoke(
            app,
            ["env", "init"],
            input=f"y\ny\n{user_name}\n{password}\n{port}\n{database}\n1800\n1\n",
        )

        assert result.exit_code == 0

        env = dotenv_values(Path(".env"))

        assert env["DEBUG"] == "1"
        assert env["PROFILING"] == "1"
        assert env["JWT_EXPIRATION_TIME"] == "1800"
        assert len(env["JWT_SECRET_KEY"]) == 256
        assert env["COMPETITION"] == "world_cup_2022"
        assert env["LOCK_DATETIME"] == "2022-11-20 17:00:00+01:00"
        assert env["BASE_CORRECT_RESULT"] == "1"
        assert env["MULTIPLYING_FACTOR_CORRECT_RESULT"] == "2"
        assert env["BASE_CORRECT_SCORE"] == "3"
        assert env["MULTIPLYING_FACTOR_CORRECT_SCORE"] == "7"
        assert env["TEAM_QUALIFIED"] == "10"
        assert env["FIRST_TEAM_QUALIFIED"] == "20"
        assert env["DATA_FOLDER"].endswith("yak_server/data/world_cup_2022")
        assert len(json.loads(env["RULES"])) == 1

        env_mysql = dotenv_values(Path(".env.mysql"))

        assert env_mysql["MYSQL_USER_NAME"] == user_name
        assert env_mysql["MYSQL_PASSWORD"] == password
        assert env_mysql["MYSQL_PORT"] == str(port)
        assert env_mysql["MYSQL_DB"] == database


def test_yak_env_init_production() -> None:
    with runner.isolated_filesystem():
        result = runner.invoke(
            app,
            ["env", "init"],
            input="n\ny\ny\n3000\ndb\n1800\n1\n",
        )

        assert result.exit_code == 0

        env = dotenv_values(Path(".env"))

        assert env["DEBUG"] == "0"
        assert "PROFILING" not in env
