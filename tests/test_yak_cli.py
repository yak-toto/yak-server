import os
import subprocess
from datetime import datetime, timedelta, timezone
from http import HTTPStatus
from pathlib import Path
from typing import TYPE_CHECKING

import pexpect
from dateutil import parser
from starlette.testclient import TestClient

from .utils import get_random_string

if TYPE_CHECKING:
    from fastapi import FastAPI


def test_cli(app_with_valid_jwt_config: "FastAPI"):
    # Check database drop
    result = subprocess.run(
        ["yak", "db", "drop"],
        capture_output=True,
        env={**os.environ, "DEBUG": "1"},
    )

    assert result.returncode == 0

    # Check database creation
    result = subprocess.run(
        ["yak", "db", "create"],
        capture_output=True,
    )

    assert result.returncode == 0

    # Check database initialization
    data_folder = str((Path(__file__).parents[1] / "yak_server/data/world_cup_2022").resolve())

    result = subprocess.run(
        ["yak", "db", "init"],
        capture_output=True,
        env={
            **os.environ,
            "JWT_EXPIRATION_TIME": "1800",
            "JWT_SECRET_KEY": get_random_string(128),
            "COMPETITION": "world_cup_2022",
            "DATA_FOLDER": data_folder,
            "LOCK_DATETIME": str(datetime.now(tz=timezone.utc)),
            "BASE_CORRECT_RESULT": "1",
            "MULTIPLYING_FACTOR_CORRECT_RESULT": "1",
            "BASE_CORRECT_SCORE": "1",
            "MULTIPLYING_FACTOR_CORRECT_SCORE": "1",
            "TEAM_QUALIFIED": "10",
            "FIRST_TEAM_QUALIFIED": "20",
            "RULES": "[]",
        },
    )

    assert result.returncode == 0

    # Check admin account creation
    admin_password = get_random_string(7)

    child = pexpect.spawn(
        "yak db admin",
        env={
            **os.environ,
            "JWT_EXPIRATION_TIME": "1800",
            "JWT_SECRET_KEY": get_random_string(128),
            "COMPETITION": "world_cup_2022",
            "DATA_FOLDER": data_folder,
            "LOCK_DATETIME": str(datetime.now(tz=timezone.utc)),
            "BASE_CORRECT_RESULT": "1",
            "MULTIPLYING_FACTOR_CORRECT_RESULT": "1",
            "BASE_CORRECT_SCORE": "1",
            "MULTIPLYING_FACTOR_CORRECT_SCORE": "1",
            "TEAM_QUALIFIED": "10",
            "FIRST_TEAM_QUALIFIED": "20",
            "RULES": "[]",
        },
    )

    child.expect("Admin user password: ", timeout=100)
    child.sendline(admin_password)
    child.expect("Confirm admin password: ", timeout=100)
    child.sendline(admin_password)
    child.expect(pexpect.EOF)

    child.close()

    assert child.exitstatus == 0
    assert child.signalstatus is None

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
    result = subprocess.run(
        ["yak", "db", "backup"],
        capture_output=True,
    )

    assert result.returncode == 0

    list_datetime_backup = sorted(
        parser.parse(file.name.replace(".sql", "").replace("yak_toto_backup_", ""))
        for file in (Path(__file__).parents[1] / "yak_server/cli/backup_files").glob("*")
    )

    # Check that most recent backup file has been created less than 2 seconds ago
    assert datetime.now(tz=timezone.utc) - list_datetime_backup[-1] <= timedelta(seconds=2)

    # Check records deletion
    result = subprocess.run(
        ["yak", "db", "delete"],
        capture_output=True,
        env={**os.environ, "DEBUG": "1"},
    )

    assert result.returncode == 0

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

    # Test the migration helper command line
    result = subprocess.run(
        ["yak", "db", "migration"],
        capture_output=True,
    )

    assert result.returncode == 0
