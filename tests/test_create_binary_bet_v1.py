from datetime import datetime, timedelta
from http import HTTPStatus
from importlib import resources
from unittest.mock import ANY
from uuid import uuid4

import pytest

from yak_server.cli.database import initialize_database

from .utils import get_random_string


@pytest.fixture()
def setup_app(app):
    # location of test data
    with resources.as_file(resources.files("tests") / "test_data/test_create_bet") as path:
        app.config["DATA_FOLDER"] = path
    old_lock_datetime = app.config["LOCK_DATETIME"]
    app.config["LOCK_DATETIME"] = str(datetime.now() + timedelta(minutes=10))

    with app.app_context():
        initialize_database(app)

    yield app

    app.config["LOCK_DATETIME"] = old_lock_datetime


def test_create_binary_bet(client, setup_app):
    # Signup one user
    response_signup = client.post(
        "/api/v1/users/signup",
        json={
            "name": get_random_string(6),
            "first_name": get_random_string(6),
            "last_name": get_random_string(6),
            "password": get_random_string(6),
        },
    )

    assert response_signup.status_code == HTTPStatus.CREATED

    token = response_signup.json["result"]["token"]

    # Fetch all teams
    response_all_teams = client.get("/api/v1/teams")

    assert response_all_teams.status_code == HTTPStatus.OK

    team1 = response_all_teams.json["result"]["teams"][0]
    team2 = response_all_teams.json["result"]["teams"][1]
    is_one_won = True

    # Fetch all groups
    response_all_groups = client.get("/api/v1/groups", headers={"Authorization": f"Bearer {token}"})

    assert response_all_groups.status_code == HTTPStatus.OK

    group_id = response_all_groups.json["result"]["groups"][0]["id"]

    # Create one binary bet
    response_create_binary_bet = client.post(
        "/api/v1/binary_bets",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "is_one_won": is_one_won,
            "index": 1,
            "team1": {"id": team1["id"]},
            "team2": {"id": team2["id"]},
            "group": {"id": group_id},
        },
    )

    binary_bet_response = {
        "ok": True,
        "result": {
            "group": {
                "code": "A",
                "description": "Groupe A",
                "id": group_id,
            },
            "phase": {
                "code": "GROUP",
                "description": "Group stage",
                "id": ANY,
            },
            "binary_bet": {
                "id": ANY,
                "index": 1,
                "locked": False,
                "team1": team1 | {"won": True},
                "team2": team2 | {"won": False},
            },
        },
    }

    assert response_create_binary_bet.json == binary_bet_response

    binary_bet_id = response_create_binary_bet.json["result"]["binary_bet"]["id"]

    # Check GET after POST
    response_retrieve_one_bet = client.get(
        f"/api/v1/binary_bets/{binary_bet_id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response_retrieve_one_bet.status_code == HTTPStatus.OK
    assert response_retrieve_one_bet.json == binary_bet_response

    # Check POST with invalid group id
    invalid_group_id = str(uuid4())

    response_create_binary_bet_with_group_id = client.post(
        "/api/v1/binary_bets",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "index": 1,
            "team1": {"id": team1["id"]},
            "team2": {"id": team2["id"]},
            "group": {"id": invalid_group_id},
        },
    )

    assert response_create_binary_bet_with_group_id.status_code == HTTPStatus.NOT_FOUND
    assert response_create_binary_bet_with_group_id.json == {
        "ok": False,
        "error_code": HTTPStatus.NOT_FOUND,
        "description": f"Group not found: {invalid_group_id}",
    }

    # Check POST with invalid team1 id
    invalid_team1_id = str(uuid4())

    response_create_binary_bet_with_team1_id = client.post(
        "/api/v1/binary_bets",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "index": 1,
            "team1": {"id": invalid_team1_id},
            "team2": {"id": team2["id"]},
            "group": {"id": group_id},
        },
    )

    assert response_create_binary_bet_with_team1_id.status_code == HTTPStatus.NOT_FOUND
    assert response_create_binary_bet_with_team1_id.json == {
        "ok": False,
        "error_code": HTTPStatus.NOT_FOUND,
        "description": f"Team not found: {invalid_team1_id}",
    }

    # Check POST with invalid team2 id
    invalid_team2_id = str(uuid4())

    response_create_binary_bet_with_team2_id = client.post(
        "/api/v1/binary_bets",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "index": 1,
            "team1": {"id": team1["id"]},
            "team2": {"id": invalid_team2_id},
            "group": {"id": group_id},
        },
    )

    assert response_create_binary_bet_with_team2_id.status_code == HTTPStatus.NOT_FOUND
    assert response_create_binary_bet_with_team2_id.json == {
        "ok": False,
        "error_code": HTTPStatus.NOT_FOUND,
        "description": f"Team not found: {invalid_team2_id}",
    }

    # Check bet locking
    old_lock_datetime = setup_app.config["LOCK_DATETIME"]
    setup_app.config["LOCK_DATETIME"] = str(datetime.now() - timedelta(minutes=10))

    response_create_locked_binary_bet = client.post(
        "/api/v1/binary_bets",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "index": 1,
            "team1": {"id": team1["id"]},
            "team2": {"id": team2["id"]},
            "group": {"id": group_id},
        },
    )

    assert response_create_locked_binary_bet.status_code == HTTPStatus.UNAUTHORIZED
    assert response_create_locked_binary_bet.json == {
        "ok": False,
        "error_code": HTTPStatus.UNAUTHORIZED,
        "description": "Cannot modify bets because locked date is exceeded",
    }

    setup_app.config["LOCK_DATETIME"] = old_lock_datetime
