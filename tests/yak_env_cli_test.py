import json
from pathlib import Path
from secrets import randbelow

import pytest
from click.testing import CliRunner
from dotenv import dotenv_values

from testing.util import get_random_string
from yak_server.cli import app

runner = CliRunner()


def test_yak_env_all() -> None:
    host = get_random_string(10)
    user_name = get_random_string(15)
    password = get_random_string(250)
    port = randbelow(80000)
    database = get_random_string(15)

    with runner.isolated_filesystem():
        result = runner.invoke(
            app,
            ["env", "all"],
            input=f"y\n{host}\n{user_name}\n{password}\n{port}\n{database}\n1800\n1800\nworld_cup_2022\n",
        )

        assert result.exit_code == 0

        env = dotenv_values(Path(".env"))

        assert env["DEBUG"] == "1"
        assert env["JWT_EXPIRATION_TIME"] == "1800"
        assert env["JWT_SECRET_KEY"] is not None
        assert len(env["JWT_SECRET_KEY"]) == 256
        assert env["JWT_REFRESH_SECRET_KEY"] is not None
        assert len(env["JWT_REFRESH_SECRET_KEY"]) == 256
        assert env["COMPETITION"] == "world_cup_2022"
        assert env["LOCK_DATETIME"] == "2022-11-20T17:00:00+01:00"
        assert env["OFFICIAL_RESULTS_URL"] == "https://en.wikipedia.org/wiki/2022_FIFA_World_Cup"
        assert env["DATA_FOLDER"] is not None
        assert Path(env["DATA_FOLDER"]).samefile(
            Path(__file__).parents[1] / "yak_server" / "data" / "world_cup_2022",
        )
        assert env["RULES"] is not None
        assert len(json.loads(env["RULES"])) == 2

        env_db = dotenv_values(Path(".env.db"))

        assert env_db["POSTGRES_HOST"] == host
        assert env_db["POSTGRES_USER"] == user_name
        assert env_db["POSTGRES_PASSWORD"] == password
        assert env_db["POSTGRES_PORT"] == str(port)
        assert env_db["POSTGRES_DB"] == database


def test_yak_env_all_production() -> None:
    with runner.isolated_filesystem():
        result = runner.invoke(
            app,
            ["env", "all"],
            input="n\nlocalhost\nroot\ny\n3000\ndb\n1800\n1800\neuro_2016\n",
        )

        assert result.exit_code == 0

        env = dotenv_values(Path(".env"))

        assert env["DEBUG"] == "0"


def test_yak_env_all_world_cup_2018() -> None:
    with runner.isolated_filesystem():
        result = runner.invoke(
            app,
            ["env", "all"],
            input="y\nroot\nroot\ndddddddd\n\ndb\n1800\n1800\nworld_cup_2018\n",
        )

        assert result.exit_code == 0

        env = dotenv_values(Path(".env"))

        assert env["RULES"] is not None
        assert json.loads(env["RULES"]) == {}


def test_yak_env_all_invalid_lockdatetime(monkeypatch: pytest.MonkeyPatch) -> None:
    with runner.isolated_filesystem() as tmpdir:
        date = "2022-11-12"

        (Path(tmpdir) / "data" / "competition0").mkdir(parents=True)
        (Path(tmpdir) / "data" / "competition0" / "common.json").write_text(
            json.dumps({"lock_datetime": date, "official_results_url": ""}),
        )

        monkeypatch.setattr("yak_server.cli.env.__file__", (Path(tmpdir) / "e" / "e").resolve())

        result = runner.invoke(
            app,
            ["env", "all"],
            input="n\nlocalhost\nroot\ny\n3000\ndb\n1800\n1800\ncompetition0\n",
            catch_exceptions=True,
        )

        assert result.exit_code == 1
        assert "Input should have timezone info" in str(result.exception)


def test_yak_env_db() -> None:
    host = get_random_string(10)
    user_name = get_random_string(56)
    password = get_random_string(12)
    port = randbelow(50000)
    database = get_random_string(20)

    with runner.isolated_filesystem():
        result = runner.invoke(
            app,
            ["env", "db"],
            input=f"{host}\n{user_name}\n{password}\n{port}\n{database}\n",
        )

        assert result.exit_code == 0

        env_db = dotenv_values(Path(".env.db"))

        assert env_db["POSTGRES_HOST"] == host
        assert env_db["POSTGRES_USER"] == user_name
        assert env_db["POSTGRES_PASSWORD"] == password
        assert env_db["POSTGRES_PORT"] == str(port)
        assert env_db["POSTGRES_DB"] == database


def test_yak_env_app() -> None:
    with runner.isolated_filesystem():
        result = runner.invoke(
            app,
            ["env", "app"],
            input="y\n1800\n1800\nworld_cup_2018\n",
        )

        assert result.exit_code == 0

        env = dotenv_values(Path(".env"))

        assert env["DEBUG"] == "1"
        assert env["JWT_EXPIRATION_TIME"] == "1800"
        assert env["JWT_SECRET_KEY"] is not None
        assert len(env["JWT_SECRET_KEY"]) == 256
        assert env["JWT_REFRESH_SECRET_KEY"] is not None
        assert len(env["JWT_REFRESH_SECRET_KEY"]) == 256
        assert env["COMPETITION"] == "world_cup_2018"
        assert env["LOCK_DATETIME"] == "2018-06-14T18:00:00+03:00"
        assert env["OFFICIAL_RESULTS_URL"] == "https://en.wikipedia.org/wiki/2018_FIFA_World_Cup"
        assert env["DATA_FOLDER"] is not None
        assert Path(env["DATA_FOLDER"]).samefile(
            Path(__file__).parents[1] / "yak_server" / "data" / "world_cup_2018",
        )
        assert env["RULES"] is not None
        assert len(json.loads(env["RULES"])) == 0
