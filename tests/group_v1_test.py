from http import HTTPStatus
from typing import TYPE_CHECKING
from unittest.mock import ANY

from starlette.testclient import TestClient

from testing.util import get_random_string, get_resources_path
from yak_server.cli.database import initialize_database

if TYPE_CHECKING:
    from fastapi import FastAPI
    from sqlalchemy import Engine


def test_group(app_with_valid_jwt_config: "FastAPI", engine_for_test: "Engine") -> None:
    initialize_database(
        engine_for_test, app_with_valid_jwt_config, get_resources_path("test_matches_db")
    )

    client = TestClient(app_with_valid_jwt_config)

    # Signup one random user
    user_name = get_random_string(6)
    first_name = get_random_string(10)
    last_name = get_random_string(8)
    password = get_random_string(100)

    response_signup = client.post(
        "/api/v1/users/signup",
        json={
            "name": user_name,
            "first_name": first_name,
            "last_name": last_name,
            "password": password,
        },
    )

    auth_token = response_signup.json()["result"]["access_token"]

    # Check all GET matches response
    expected_group = {"id": ANY, "code": "A", "phase": {"id": ANY}, "description": "Groupe A"}

    expected_group_without_phase = {
        key: value for key, value in expected_group.items() if key != "phase"
    }

    expected_phase = {
        "code": "GROUP",
        "description": "Phase de groupes",
        "id": ANY,
    }

    # Check groups associated to one phase
    group_response = client.get(
        "/api/v1/groups/phases/GROUP",
        headers={"Authorization": f"Bearer {auth_token}"},
    )

    assert group_response.status_code == HTTPStatus.OK
    assert group_response.json()["result"] == {
        "phase": expected_phase,
        "groups": [expected_group_without_phase],
    }

    # Check groups by phase with invalid phase identifier
    invalid_phase_code = get_random_string(5)

    group_response_invalid_phase_code = client.get(
        f"/api/v1/groups/phases/{invalid_phase_code}",
        headers={"Authorization": f"Bearer {auth_token}"},
    )

    assert group_response_invalid_phase_code.status_code == HTTPStatus.NOT_FOUND
    assert group_response_invalid_phase_code.json() == {
        "ok": False,
        "error_code": HTTPStatus.NOT_FOUND,
        "description": f"Phase not found: {invalid_phase_code}",
    }

    # Check GET /groups/{group_code}
    one_group_response = client.get(
        "/api/v1/groups/A",
        headers={"Authorization": f"Bearer {auth_token}"},
    )

    assert one_group_response.status_code == HTTPStatus.OK
    assert one_group_response.json()["result"] == {
        "group": expected_group_without_phase,
        "phase": expected_phase,
    }

    # Check GET /groups/{groupCode} with invalid code
    invalid_group_code = "B"

    group_response_with_invalid_code = client.get(
        "/api/v1/groups/B",
        headers={"Authorization": f"Bearer {auth_token}"},
    )

    assert group_response_with_invalid_code.status_code == HTTPStatus.NOT_FOUND
    assert group_response_with_invalid_code.json() == {
        "ok": False,
        "error_code": HTTPStatus.NOT_FOUND,
        "description": f"Group not found: {invalid_group_code}",
    }

    # Check GET /groups
    all_groups_response = client.get(
        "/api/v1/groups",
        headers={"Authorization": f"Bearer {auth_token}"},
    )

    assert all_groups_response.status_code == HTTPStatus.OK
    assert all_groups_response.json()["result"] == {
        "phases": [expected_phase],
        "groups": [expected_group],
    }
