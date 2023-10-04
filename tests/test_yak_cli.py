import os
from http import HTTPStatus
from pathlib import Path
from typing import TYPE_CHECKING

import pendulum
from starlette.testclient import TestClient
from typer.testing import CliRunner

from yak_server.cli import app

from .utils import get_random_string

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
    data_folder = str((Path(__file__).parents[1] / "yak_server/data/world_cup_2022").resolve())

    result = runner.invoke(
        app,
        ["db", "init"],
        env={
            "JWT_EXPIRATION_TIME": "1800",
            "JWT_SECRET_KEY": get_random_string(128),
            "COMPETITION": "world_cup_2022",
            "DATA_FOLDER": data_folder,
            "LOCK_DATETIME": str(pendulum.now("UTC")),
            "RULES": "{}",
        },
    )

    assert result.exit_code == 0

    # Check admin account creation
    admin_password = get_random_string(7)

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

    auth_token = response_login.json()["result"]["token"]
    user_id = response_login.json()["result"]["id"]

    # Check backup command
    result = runner.invoke(app, ["db", "backup"])

    assert result.exit_code == 0

    list_datetime_backup = sorted(
        pendulum.parse(file.name.replace(".sql", "").replace("yak_toto_backup_", ""))
        for file in (Path(__file__).parents[1] / "yak_server/cli/backup_files").glob("*")
    )

    # Check that most recent backup file has been created less than 2 seconds ago
    assert pendulum.now("UTC") - list_datetime_backup[-1] <= pendulum.duration(seconds=2)

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

    # Check the same error with v2 api
    response_login_user_not_found_v2 = client.post(
        "/api/v2",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={
            "query": """
                query {
                    currentUserResult {
                        __typename
                        ... on User {
                            fullName
                        }
                        ... on InvalidToken {
                            message
                        }
                        ... on ExpiredToken {
                            message
                        }
                    }
                }
            """,
        },
    )

    assert response_login_user_not_found_v2.json() == {
        "data": {
            "currentUserResult": {
                "__typename": "InvalidToken",
                "message": "Invalid token, authentication required",
            },
        },
    }


def test_db_migration_cli_with_alembic_present() -> None:
    result = runner.invoke(app, ["db", "migration"])

    assert result.exit_code == 0


def test_db_migration_cli_with_alembic_missing(monkeypatch: "pytest.MonkeyPatch") -> None:
    monkeypatch.setattr("yak_server.cli.database.alembic", None)

    result = runner.invoke(app, ["db", "migration"])

    assert result.exit_code == 0
    assert "To enable migration using alembic, please run: pip install alembic" in result.output
