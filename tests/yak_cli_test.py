import json
import os
from http import HTTPStatus
from importlib.metadata import version
from pathlib import Path
from typing import TYPE_CHECKING

import pendulum
from click.testing import CliRunner
from starlette.testclient import TestClient

from testing.util import get_random_string
from yak_server.cli import app

if TYPE_CHECKING:
    import pytest
    from fastapi import FastAPI

runner = CliRunner()


def test_cli(app_with_valid_jwt_config: "FastAPI") -> None:
    # Check database drop
    result = runner.invoke(app, ["db", "drop"], env={"DEBUG": "1"})

    assert result.exit_code == 0

    # Check database creation
    result = runner.invoke(app, ["db", "create"])

    assert result.exit_code == 0

    # Check database initialization
    data_folder = str(Path(__file__).parents[1] / "yak_server" / "data" / "world_cup_2022")

    result = runner.invoke(
        app,
        ["db", "init"],
        env={
            "JWT_EXPIRATION_TIME": "1800",
            "JWT_REFRESH_EXPIRATION_TIME": "1800",
            "JWT_SECRET_KEY": get_random_string(128),
            "COMPETITION": "world_cup_2022",
            "DATA_FOLDER": data_folder,
            "LOCK_DATETIME": str(pendulum.now("UTC")),
            "RULES": "{}",
            "OFFICIAL_RESULTS_URL": "https://en.wikipedia.org/wiki/2022_FIFA_World_Cup",
        },
    )

    assert result.exit_code == 0

    # Check admin account creation
    admin_password = get_random_string(9)

    result = runner.invoke(
        app,
        ["db", "admin"],
        env={
            "JWT_EXPIRATION_TIME": "1800",
            "JWT_SECRET_KEY": get_random_string(128),
            "COMPETITION": "world_cup_2022",
            "DATA_FOLDER": data_folder,
            "LOCK_DATETIME": str(pendulum.now("UTC")),
            "RULES": "{}",
        },
        input=f"{admin_password}\n{admin_password}\n",
    )

    assert result.exit_code == 0

    client = TestClient(app_with_valid_jwt_config)

    response_login = client.post(
        "/api/v1/users/login",
        json={
            "name": "admin",
            "password": admin_password,
        },
    )

    assert response_login.status_code == HTTPStatus.CREATED

    auth_token = response_login.json()["result"]["access_token"]
    user_id = response_login.json()["result"]["id"]

    # Check records deletion
    result = runner.invoke(app, ["db", "delete"], env={**os.environ, "DEBUG": "1"})

    assert result.exit_code == 0

    # Check user cannot access after records are cleaned
    response_login_user_not_found = client.get(
        "/api/v1/bets",
        headers={"Authorization": f"Bearer {auth_token}"},
    )

    assert response_login_user_not_found.status_code == HTTPStatus.NOT_FOUND
    assert response_login_user_not_found.json() == {
        "ok": False,
        "error_code": HTTPStatus.NOT_FOUND,
        "description": f"User not found: {user_id}",
    }


def test_cli_admin_already_exists() -> None:
    # Check admin account creation
    admin_password = get_random_string(9)

    result = runner.invoke(
        app,
        ["db", "admin"],
        input=f"{admin_password}\n{admin_password}\n",
    )

    admin_already_exists_message = "Admin already exists"

    assert result.exit_code == 0
    assert admin_already_exists_message not in result.stdout

    result = runner.invoke(
        app,
        ["db", "admin"],
        input=f"{admin_password}\n{admin_password}\n",
    )

    assert result.exit_code == 0
    assert admin_already_exists_message in result.stdout


def test_db_migration_cli_with_alembic_present() -> None:
    result = runner.invoke(app, ["db", "migration"])

    assert result.exit_code == 0


def test_db_migration_cli_short_option() -> None:
    result = runner.invoke(app, ["db", "migration", "--short"])

    alembic_ini_path = (Path(__file__).parents[1] / "alembic.ini").resolve()

    assert result.exit_code == 0
    assert result.output == f"export ALEMBIC_CONFIG={alembic_ini_path}\n"

    result_with_short_name = result = runner.invoke(app, ["db", "migration", "-s"])

    assert result_with_short_name.exit_code == result.exit_code
    assert result_with_short_name.output == result.output


def test_db_migration_second_path(monkeypatch: "pytest.MonkeyPatch") -> None:
    """
    .
    └── yak-server
        └── yak_server
            └── alembic.ini
    """

    with runner.isolated_filesystem():
        yak_server_module = (Path.cwd() / "yak-server" / "yak_server").resolve()

        python_file_path = yak_server_module / "cli" / "database" / "__init__.py"
        alembic_ini_path = yak_server_module / "alembic.ini"

        alembic_ini_path.parent.mkdir(parents=True)
        alembic_ini_path.touch()

        monkeypatch.setattr("yak_server.cli.database.__file__", str(python_file_path))

        result = runner.invoke(app, ["db", "migration", "-s"])

        assert result.exit_code == 0
        assert result.output == f"export ALEMBIC_CONFIG={alembic_ini_path}\n"


def test_db_migration_cli_with_alembic_missing(monkeypatch: "pytest.MonkeyPatch") -> None:
    monkeypatch.setattr("yak_server.cli.database.alembic", None)

    result = runner.invoke(app, ["db", "migration"])

    assert result.exit_code == 0
    assert (
        "To enable migration using alembic, please run: uv pip install yak-server[db_migration]"
        in result.output
    )


def test_get_openapi_spec() -> None:
    """
    Test that the OpenAPI spec is generated correctly.
    """

    result = runner.invoke(app, ["openapi"])

    assert result.exit_code == 0

    openapi_spec = json.loads(result.output)

    assert openapi_spec["openapi"] == "3.1.0"
    assert openapi_spec["info"]["version"] == version("yak-server")
    assert "paths" in openapi_spec
    assert "components" in openapi_spec
