from http import HTTPStatus
from typing import TYPE_CHECKING
from unittest.mock import ANY

import pendulum

from testing.mock import MockSettings
from testing.util import get_random_string
from yak_server.cli.database import initialize_database
from yak_server.helpers.settings import get_settings

if TYPE_CHECKING:
    import pytest
    from fastapi import FastAPI
    from starlette.testclient import TestClient


def test_group(app: "FastAPI", client: "TestClient", monkeypatch: "pytest.MonkeyPatch") -> None:
    fake_jwt_secret_key = get_random_string(100)

    app.dependency_overrides[get_settings] = MockSettings(
        jwt_secret_key=fake_jwt_secret_key,
        jwt_expiration_time=10,
        lock_datetime_shift=pendulum.duration(minutes=10),
    )

    monkeypatch.setattr(
        "yak_server.cli.database.get_settings",
        MockSettings(data_folder_relative="test_matches_db"),
    )

    initialize_database(app)

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

    auth_token = response_signup.json()["result"]["token"]

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
