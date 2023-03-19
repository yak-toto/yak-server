from http import HTTPStatus
from importlib import resources
from unittest.mock import ANY
from uuid import uuid4

import pytest

from yak_server.cli.database import initialize_database

from .utils import get_random_string


@pytest.fixture(autouse=True)
def setup_app(app):
    testcase = "test_phase_v1"

    # location of test data
    with resources.as_file(resources.files("tests") / testcase) as path:
        app.config["DATA_FOLDER"] = path

    # initialize sql database
    with app.app_context():
        initialize_database(app)

    return app


def test_phase(client):
    # Signup one random user
    user_name = get_random_string(6)
    first_name = get_random_string(10)
    last_name = get_random_string(8)
    password = get_random_string(5)

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

    token = response_signup.json["result"]["token"]

    # Success case : retrieve all phases
    response_all_phases = client.get("/api/v1/phases", headers={"Authorization": f"Bearer {token}"})

    assert response_all_phases.status_code == HTTPStatus.OK
    assert response_all_phases.json == {
        "ok": True,
        "result": [
            {"code": "GROUP", "description": "Group stage", "id": ANY},
            {"code": "FINAL", "description": "Final stage", "id": ANY},
        ],
    }

    # Success case : retrieve phase by id
    phase_id = response_all_phases.json["result"][0]["id"]

    response_phase_by_id = client.get(
        f"/api/v1/phases/{phase_id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response_phase_by_id.status_code == HTTPStatus.OK
    assert response_phase_by_id.json == {
        "ok": True,
        "result": {"code": "GROUP", "description": "Group stage", "id": phase_id},
    }

    # Error case : retrieve phase by invalid id
    invalid_phase_id = str(uuid4())

    response_phase_with_invalid_id = client.get(
        f"/api/v1/phases/{invalid_phase_id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response_phase_with_invalid_id.status_code == HTTPStatus.NOT_FOUND
    assert response_phase_with_invalid_id.json == {
        "ok": False,
        "error_code": HTTPStatus.NOT_FOUND,
        "description": f"Phase not found: {invalid_phase_id}",
    }
