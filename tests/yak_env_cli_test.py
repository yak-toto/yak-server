import json
from pathlib import Path
from secrets import randbelow

import pytest
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
            input=f"y\n{host}\n{user_name}\n{password}\n{port}\n{database}\n1800\nworld_cup_2022\n",
        )

        assert result.exit_code == 0

        env = dotenv_values(Path(".env"))

        assert env["DEBUG"] == "1"
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

        env_db = dotenv_values(Path(".env.db"))

        assert env_db["POSTGRES_HOST"] == host
        assert env_db["POSTGRES_USER"] == user_name
        assert env_db["POSTGRES_PASSWORD"] == password
        assert env_db["POSTGRES_PORT"] == str(port)
        assert env_db["POSTGRES_DB"] == database


def test_yak_env_init_production() -> None:
    with runner.isolated_filesystem():
        result = runner.invoke(
            app,
            ["env", "init"],
            input="n\ny\nroot\ny\n3000\ndb\n1800\neuro_2016\n",
        )

        assert result.exit_code == 0

        env = dotenv_values(Path(".env"))

        assert env["DEBUG"] == "0"


def test_yak_env_init_world_cup_2018() -> None:
    with runner.isolated_filesystem():
        result = runner.invoke(
            app,
            ["env", "init"],
            input="y\ny\nroot\nroot\ndddddddd\n\ndb\n1800\nworld_cup_2018\n",
        )

        assert result.exit_code == 0

        env = dotenv_values(Path(".env"))

        assert env["RULES"] is not None
        assert json.loads(env["RULES"]) == {}


def test_yak_env_init_invalid_lockdatetime(monkeypatch: pytest.MonkeyPatch) -> None:
    with runner.isolated_filesystem() as tmpdir:
        date = "2022-11-12"

        (Path(tmpdir) / "data" / "competition0").mkdir(parents=True)
        (Path(tmpdir) / "data" / "competition0" / "common.json").write_text(
            json.dumps({"lock_datetime": date, "official_results_url": ""})
        )

        monkeypatch.setattr("yak_server.cli.env.__file__", (Path(tmpdir) / "e" / "e").resolve())

        result = runner.invoke(
            app,
            ["env", "init"],
            input="n\ny\nroot\ny\n3000\ndb\n1800\ncompetition0\n",
            catch_exceptions=True,
        )

        assert result.exit_code == 1
        assert str(result.exception) == f"lock_datetime is not a valid datetime: {date}"
