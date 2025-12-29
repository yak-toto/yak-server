from datetime import datetime, timedelta, timezone
from http import HTTPStatus
from typing import TYPE_CHECKING
from unittest.mock import ANY
from uuid import uuid4

from starlette.testclient import TestClient

from testing.mock import MockLockDatetime
from testing.util import get_random_string, get_resources_path
from yak_server.cli.database import initialize_database
from yak_server.helpers.settings import get_lock_datetime

if TYPE_CHECKING:
    from fastapi import FastAPI
    from sqlalchemy import Engine


def test_binary_bet(app_with_valid_jwt_config: "FastAPI", engine_for_test: "Engine") -> None:
    initialize_database(
        engine_for_test, app_with_valid_jwt_config, get_resources_path("test_binary_bet")
    )

    client = TestClient(app_with_valid_jwt_config)

    response_signup = client.post(
        "/api/v1/users/signup",
        json={
            "name": get_random_string(2),
            "first_name": get_random_string(6),
            "last_name": get_random_string(12),
            "password": get_random_string(10),
        },
    )

    assert response_signup.status_code == HTTPStatus.CREATED

    access_token = response_signup.json()["result"]["access_token"]

    response_bets = client.get("/api/v1/bets", headers={"Authorization": f"Bearer {access_token}"})

    assert response_bets.status_code == HTTPStatus.OK

    bet_id = response_bets.json()["result"]["binary_bets"][0]["id"]

    response_modify_binary_bet = client.patch(
        f"/api/v1/binary_bets/{bet_id}",
        headers={"Authorization": f"Bearer {access_token}"},
        json={"is_one_won": True},
    )

    assert response_modify_binary_bet.status_code == HTTPStatus.OK
    assert response_modify_binary_bet.json() == {
        "ok": True,
        "result": {
            "phase": {"code": "GROUP", "description": "Phase de groupes", "id": ANY},
            "group": {"code": "A", "description": "Groupe A", "id": ANY},
            "binary_bet": {
                "id": ANY,
                "locked": False,
                "team1": {
                    "code": "FR",
                    "description": "France",
                    "flag": {"url": ANY},
                    "id": ANY,
                    "won": True,
                },
                "team2": {
                    "code": "GR",
                    "description": "Allemagne",
                    "flag": {"url": ANY},
                    "id": ANY,
                    "won": False,
                },
            },
        },
    }

    # Error case : locked bet
    app_with_valid_jwt_config.dependency_overrides[get_lock_datetime] = MockLockDatetime(
        datetime.now(timezone.utc) - timedelta(minutes=10),
    )

    response_lock_bet = client.patch(
        f"/api/v1/binary_bets/{bet_id}",
        headers={"Authorization": f"Bearer {access_token}"},
        json={"is_one_won": True},
    )

    assert response_lock_bet.status_code == HTTPStatus.UNAUTHORIZED
    assert response_lock_bet.json() == {
        "ok": False,
        "error_code": HTTPStatus.UNAUTHORIZED,
        "description": "Cannot modify binary bet, lock date is exceeded",
    }

    app_with_valid_jwt_config.dependency_overrides[get_lock_datetime] = MockLockDatetime(
        datetime.now(timezone.utc) + timedelta(minutes=10),
    )

    # Error case : Invalid input
    response_invalid_inputs = client.patch(
        f"/api/v1/binary_bets/{bet_id}",
        headers={"Authorization": f"Bearer {access_token}"},
        json={"is_won": True},
    )

    assert response_invalid_inputs.status_code == HTTPStatus.UNPROCESSABLE_ENTITY

    # Error case : invalid bet id
    invalid_bet_id = uuid4()

    response_with_invalid_bet_id = client.patch(
        f"/api/v1/binary_bets/{invalid_bet_id}",
        headers={"Authorization": f"Bearer {access_token}"},
        json={"is_one_won": True},
    )

    assert response_with_invalid_bet_id.status_code == HTTPStatus.NOT_FOUND
    assert response_with_invalid_bet_id.json() == {
        "ok": False,
        "error_code": HTTPStatus.NOT_FOUND,
        "description": f"Bet not found: {invalid_bet_id}",
    }

    # Success case : retrieve one binary bet
    response_binary_bet_by_id = client.get(
        f"/api/v1/binary_bets/{bet_id}",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert response_binary_bet_by_id.status_code == HTTPStatus.OK
    assert response_binary_bet_by_id.json() == {
        "ok": True,
        "result": {
            "phase": {"code": "GROUP", "description": "Phase de groupes", "id": ANY},
            "group": {"code": "A", "description": "Groupe A", "id": ANY},
            "binary_bet": {
                "id": ANY,
                "locked": False,
                "team1": {
                    "code": "FR",
                    "description": "France",
                    "flag": {"url": ANY},
                    "id": ANY,
                    "won": True,
                },
                "team2": {
                    "code": "GR",
                    "description": "Allemagne",
                    "flag": {"url": ANY},
                    "id": ANY,
                    "won": False,
                },
            },
        },
    }

    # Error case : retrieve binary bet with invalid id
    invalid_bet_id = uuid4()

    response_retrieve_with_invalid_bet_id = client.get(
        f"/api/v1/binary_bets/{invalid_bet_id}",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert response_retrieve_with_invalid_bet_id.status_code == HTTPStatus.NOT_FOUND
    assert response_retrieve_with_invalid_bet_id.json() == {
        "ok": False,
        "error_code": HTTPStatus.NOT_FOUND,
        "description": f"Bet not found: {invalid_bet_id}",
    }

    # Success case : Modify team1 id by setting it to None
    response_change_team1_to_none = client.patch(
        f"/api/v1/binary_bets/{bet_id}",
        headers={"Authorization": f"Bearer {access_token}"},
        json={"team1": {"id": None}},
    )

    assert response_change_team1_to_none.status_code == HTTPStatus.OK
    assert response_change_team1_to_none.json()["result"]["binary_bet"] == {
        "id": bet_id,
        "locked": False,
        "team1": None,
        "team2": {
            "id": ANY,
            "code": "GR",
            "description": "Allemagne",
            "flag": ANY,
            "won": False,
        },
    }

    # Success case : Change team2
    response_all_teams = client.get("/api/v1/teams")

    team_spain = [
        team for team in response_all_teams.json()["result"]["teams"] if team["code"] == "ES"
    ]

    assert len(team_spain) == 1

    team_spain = team_spain[0]["id"]

    response_change_team2 = client.patch(
        f"/api/v1/binary_bets/{bet_id}",
        headers={"Authorization": f"Bearer {access_token}"},
        json={"team2": {"id": team_spain}},
    )

    assert response_change_team2.status_code == HTTPStatus.OK
    assert response_change_team2.json()["result"]["binary_bet"] == {
        "id": ANY,
        "locked": False,
        "team1": None,
        "team2": {
            "id": team_spain,
            "code": "ES",
            "description": "Espagne",
            "flag": ANY,
            "won": False,
        },
    }

    # Error case : modify team id with invalid team id
    invalid_team_id = str(uuid4())

    response_invalid_team1_id = client.patch(
        f"/api/v1/binary_bets/{bet_id}",
        headers={"Authorization": f"Bearer {access_token}"},
        json={"team1": {"id": invalid_team_id}},
    )

    assert response_invalid_team1_id.status_code == HTTPStatus.NOT_FOUND
    assert response_invalid_team1_id.json()["description"] == f"Team not found: {invalid_team_id}"

    response_invalid_team2_id = client.patch(
        f"/api/v1/binary_bets/{bet_id}",
        headers={"Authorization": f"Bearer {access_token}"},
        json={"team2": {"id": invalid_team_id}},
    )

    assert response_invalid_team2_id.status_code == HTTPStatus.NOT_FOUND
    assert response_invalid_team2_id.json()["description"] == f"Team not found: {invalid_team_id}"

    app_with_valid_jwt_config.dependency_overrides.clear()
