from http import HTTPStatus
from typing import TYPE_CHECKING
from unittest.mock import ANY
from uuid import uuid4

import pendulum

from testing.mock import MockSettings
from testing.util import get_random_string
from yak_server.cli.database import initialize_database
from yak_server.helpers.settings import get_settings

if TYPE_CHECKING:
    import pytest
    from fastapi import FastAPI
    from starlette.testclient import TestClient


def test_phase(app: "FastAPI", client: "TestClient", monkeypatch: "pytest.MonkeyPatch") -> None:
    fake_jwt_secret_key = get_random_string(100)

    app.dependency_overrides[get_settings] = MockSettings(
        jwt_secret_key=fake_jwt_secret_key,
        jwt_expiration_time=10,
        lock_datetime_shift=pendulum.duration(minutes=10),
    )

    monkeypatch.setattr(
        "yak_server.cli.database.get_settings",
        MockSettings(data_folder_relative="test_phase_v1"),
    )

    initialize_database(app)

    # Signup one random user
    user_name = get_random_string(6)
    first_name = get_random_string(10)
    last_name = get_random_string(8)
    password = get_random_string(21)

    response_signup = client.post(
        "/api/v1/users/signup",
        json={
            "name": user_name,
            "first_name": first_name,
            "last_name": last_name,
            "password": password,
        },
    )

    assert response_signup.status_code == HTTPStatus.CREATED

    token = response_signup.json()["result"]["token"]

    # Success case : retrieve all phases
    response_all_phases = client.get("/api/v1/phases", headers={"Authorization": f"Bearer {token}"})

    assert response_all_phases.status_code == HTTPStatus.OK
    assert response_all_phases.json() == {
        "ok": True,
        "result": [
            {"code": "GROUP", "description": "Phase de groupes", "id": ANY},
            {"code": "FINAL", "description": "Phase finale", "id": ANY},
        ],
    }

    # Success case : retrieve phase by id
    phase_id = response_all_phases.json()["result"][0]["id"]

    response_phase_by_id = client.get(
        f"/api/v1/phases/{phase_id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response_phase_by_id.status_code == HTTPStatus.OK
    assert response_phase_by_id.json() == {
        "ok": True,
        "result": {"code": "GROUP", "description": "Phase de groupes", "id": phase_id},
    }

    # Error case : retrieve phase by invalid id
    invalid_phase_id = uuid4()

    response_phase_with_invalid_id = client.get(
        f"/api/v1/phases/{invalid_phase_id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response_phase_with_invalid_id.status_code == HTTPStatus.NOT_FOUND
    assert response_phase_with_invalid_id.json() == {
        "ok": False,
        "error_code": HTTPStatus.NOT_FOUND,
        "description": f"Phase not found: {invalid_phase_id}",
    }
