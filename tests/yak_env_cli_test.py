import json
from pathlib import Path
from secrets import randbelow

from dotenv import dotenv_values
from typer.testing import CliRunner

from testing.util import get_random_string
from yak_server.cli import app

runner = CliRunner()


def test_yak_env_init() -> None:
    host = get_random_string(10)
    user_name = get_random_string(15)
    password = get_random_string(250)
    port = randbelow(80000)
    database = get_random_string(15)

    with runner.isolated_filesystem():
        result = runner.invoke(
            app,
            ["env", "init"],
            input=f"y\ny\n{host}\n{user_name}\n{password}\n{port}\n{database}\n1800\n4\n",
        )

        assert result.exit_code == 0

        env = dotenv_values(Path(".env"))

        assert env["DEBUG"] == "1"
        assert env["PROFILING"] == "1"
        assert env["JWT_EXPIRATION_TIME"] == "1800"
        assert env["JWT_SECRET_KEY"] is not None
        assert len(env["JWT_SECRET_KEY"]) == 256
        assert env["COMPETITION"] == "world_cup_2022"
        assert env["LOCK_DATETIME"] == "2022-11-20T17:00:00+01:00"
        assert env["OFFICIAL_RESULTS_URL"] == "https://en.wikipedia.org/wiki/2022_FIFA_World_Cup"
        assert env["DATA_FOLDER"] is not None
        assert Path(env["DATA_FOLDER"]).samefile(
            Path(__file__).parents[1] / "yak_server" / "data" / "world_cup_2022"
        )
        assert env["RULES"] is not None
        assert len(json.loads(env["RULES"])) == 2

        env_mysql = dotenv_values(Path(".env.mysql"))

        assert env_mysql["MYSQL_HOST"] == host
        assert env_mysql["MYSQL_USER_NAME"] == user_name
        assert env_mysql["MYSQL_PASSWORD"] == password
        assert env_mysql["MYSQL_PORT"] == str(port)
        assert env_mysql["MYSQL_DB"] == database


def test_yak_env_init_production() -> None:
    with runner.isolated_filesystem():
        result = runner.invoke(
            app,
            ["env", "init"],
            input="n\ny\nroot\ny\n3000\ndb\n1800\n1\n",
        )

        assert result.exit_code == 0

        env = dotenv_values(Path(".env"))

        assert env["DEBUG"] == "0"
        assert "PROFILING" not in env


def test_yak_env_init_world_cup_2018() -> None:
    with runner.isolated_filesystem():
        result = runner.invoke(
            app,
            ["env", "init"],
            input="y\ny\nroot\nroot\ndddddddd\n\ndb\n1800\n3\n",
        )

        assert result.exit_code == 0

        env = dotenv_values(Path(".env"))

        assert env["RULES"] is not None
        assert json.loads(env["RULES"]) == {}
