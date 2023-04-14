import json
import os
import subprocess
from base64 import b64decode
from http import HTTPStatus
from typing import TYPE_CHECKING

import pexpect

from .utils import get_random_string

if TYPE_CHECKING:
    from starlette.testclient import TestClient


def test_cli(client: "TestClient"):
    # Check database drop
    result = subprocess.run(
        "yak db drop",
        shell=True,
        capture_output=True,
        env={**os.environ, "DEBUG": "1"},
    )

    assert result.returncode == 0

    # Check database creation
    result = subprocess.run(
        "yak db create",
        shell=True,
        capture_output=True,
    )

    assert result.returncode == 0

    # Check database initialization
    result = subprocess.run(
        "yak db init",
        shell=True,
        capture_output=True,
    )

    assert result.returncode == 0

    # Check admin accoumt creation
    admin_password = get_random_string(7)

    child = pexpect.spawn("yak db admin")

    child.expect("Admin user password: ", timeout=100)
    child.sendline(f"{admin_password}\n")
    child.expect("Confirm admin password: ", timeout=100)
    child.sendline(f"{admin_password}\n")
    child.read()

    response_login = client.post(
        "/api/v1/users/login",
        json={
            "name": "admin",
            "password": admin_password,
        },
    )

    assert response_login.status_code == HTTPStatus.CREATED

    auth_token = response_login.json()["result"]["token"]

    # Check records deletion
    result = subprocess.run(
        "yak db delete",
        shell=True,
        capture_output=True,
        env={**os.environ, "DEBUG": "1"},
    )

    assert result.returncode == 0

    # Check user cannot access after records are cleaned
    response_login_user_not_found = client.get(
        "/api/v1/bets",
        headers={"Authorization": f"Bearer {auth_token}"},
    )

    user_id = json.loads(b64decode(auth_token.split(".")[1] + "=="))["sub"]

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
