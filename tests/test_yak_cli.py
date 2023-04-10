import os
import subprocess
from http import HTTPStatus

import pexpect

from .utils import get_random_string


def test_cli(client):
    # Check database drop
    result = subprocess.run(
        "yak db drop",
        shell=True,
        capture_output=True,
        env={**os.environ, "FLASK_DEBUG": "1"},
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

    auth_token = response_login.json["result"]["token"]

    # Check records deletion
    result = subprocess.run(
        "yak db delete",
        shell=True,
        capture_output=True,
        env={**os.environ, "FLASK_DEBUG": "1"},
    )

    assert result.returncode == 0

    # Check user cannot access after records are cleaned
    response_login_user_not_found = client.get(
        "/api/v1/bets",
        headers={"Authorization": f"Bearer {auth_token}"},
    )

    assert response_login_user_not_found.status_code == HTTPStatus.NOT_FOUND
    assert response_login_user_not_found.json == {
        "ok": False,
        "error_code": HTTPStatus.NOT_FOUND,
        "description": "User not found",
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

    assert response_login_user_not_found_v2.json == {
        "data": {
            "currentUserResult": {
                "__typename": "InvalidToken",
                "message": "Invalid token, authentication required",
            },
        },
    }
