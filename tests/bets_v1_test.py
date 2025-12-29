from http import HTTPStatus
from typing import TYPE_CHECKING
from unittest.mock import ANY
from uuid import uuid4

from starlette.testclient import TestClient

from testing.util import get_random_string, get_resources_path
from yak_server.cli.database import initialize_database

if TYPE_CHECKING:
    from fastapi import FastAPI
    from sqlalchemy import Engine


def test_bets(app_with_valid_jwt_config: "FastAPI", engine_for_test: "Engine") -> None:
    initialize_database(
        engine_for_test, app_with_valid_jwt_config, get_resources_path("test_modify_bet_v2")
    )

    client = TestClient(app_with_valid_jwt_config)

    user_name = get_random_string(10)
    first_name = get_random_string(5)
    last_name = get_random_string(8)
    password = get_random_string(15)

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
    authentication_token = response_signup.json()["result"]["access_token"]

    # Get all bets to retrieve ids
    response_get_all_bets = client.get(
        "/api/v1/bets",
        headers={"Authorization": f"Bearer {authentication_token}"},
    )

    assert response_get_all_bets.status_code == HTTPStatus.OK

    score_bet_ids = [
        score_bet["id"] for score_bet in response_get_all_bets.json()["result"]["score_bets"]
    ]

    # Success case : check get one bet
    response_bet_by_id = client.get(
        f"/api/v1/score_bets/{score_bet_ids[0]}",
        headers={"Authorization": f"Bearer {authentication_token}"},
    )

    assert response_bet_by_id.status_code == HTTPStatus.OK
    assert response_bet_by_id.json() == {
        "ok": True,
        "result": {
            "group": {
                "code": "A",
                "description": "Groupe A",
                "id": ANY,
            },
            "phase": {
                "code": "GROUP",
                "description": "Phase de groupes",
                "id": ANY,
            },
            "score_bet": {
                "id": ANY,
                "locked": False,
                "team1": {
                    "code": "HR",
                    "description": "Croatie",
                    "flag": {"url": ANY},
                    "id": ANY,
                    "score": None,
                },
                "team2": {
                    "code": "FI",
                    "description": "Finlande",
                    "flag": {"url": ANY},
                    "id": ANY,
                    "score": None,
                },
            },
        },
    }

    # Error case : bet with invalid id
    invalid_bet_id = uuid4()

    response_bet_with_invalid_id = client.get(
        f"/api/v1/score_bets/{invalid_bet_id}",
        headers={"Authorization": f"Bearer {authentication_token}"},
    )

    assert response_bet_with_invalid_id.status_code == HTTPStatus.NOT_FOUND
    assert response_bet_with_invalid_id.json() == {
        "ok": False,
        "error_code": HTTPStatus.NOT_FOUND,
        "description": f"Bet not found: {invalid_bet_id}",
    }

    # Success case : bet by phase
    response_by_phase = client.get(
        "/api/v1/bets/phases/GROUP",
        headers={"Authorization": f"Bearer {authentication_token}"},
    )

    assert response_by_phase.status_code == HTTPStatus.OK
    assert response_by_phase.json() == {
        "ok": True,
        "result": {
            "binary_bets": [],
            "groups": [
                {
                    "code": "A",
                    "description": "Groupe A",
                    "id": ANY,
                },
            ],
            "phase": {
                "code": "GROUP",
                "description": "Phase de groupes",
                "id": ANY,
            },
            "score_bets": [
                {
                    "group": {"id": ANY},
                    "id": ANY,
                    "locked": False,
                    "team1": {
                        "code": "HR",
                        "description": "Croatie",
                        "flag": {"url": ANY},
                        "id": ANY,
                        "score": None,
                    },
                    "team2": {
                        "code": "FI",
                        "description": "Finlande",
                        "flag": {"url": ANY},
                        "id": ANY,
                        "score": None,
                    },
                },
                {
                    "group": {"id": ANY},
                    "id": ANY,
                    "locked": False,
                    "team1": {
                        "code": "NA",
                        "description": "Namibie",
                        "flag": {"url": ANY},
                        "id": ANY,
                        "score": None,
                    },
                    "team2": {
                        "code": "IQ",
                        "description": "Irak",
                        "flag": {"url": ANY},
                        "id": ANY,
                        "score": None,
                    },
                },
                {
                    "group": {"id": ANY},
                    "id": ANY,
                    "locked": False,
                    "team1": {
                        "code": "HR",
                        "description": "Croatie",
                        "flag": {"url": ANY},
                        "id": ANY,
                        "score": None,
                    },
                    "team2": {
                        "code": "NA",
                        "description": "Namibie",
                        "flag": {"url": ANY},
                        "id": ANY,
                        "score": None,
                    },
                },
                {
                    "group": {"id": ANY},
                    "id": ANY,
                    "locked": False,
                    "team1": {
                        "code": "FI",
                        "description": "Finlande",
                        "flag": {"url": ANY},
                        "id": ANY,
                        "score": None,
                    },
                    "team2": {
                        "code": "IQ",
                        "description": "Irak",
                        "flag": {"url": ANY},
                        "id": ANY,
                        "score": None,
                    },
                },
                {
                    "group": {"id": ANY},
                    "id": ANY,
                    "locked": False,
                    "team1": {
                        "code": "HR",
                        "description": "Croatie",
                        "flag": {"url": ANY},
                        "id": ANY,
                        "score": None,
                    },
                    "team2": {
                        "code": "IQ",
                        "description": "Irak",
                        "flag": {"url": ANY},
                        "id": ANY,
                        "score": None,
                    },
                },
                {
                    "group": {"id": ANY},
                    "id": ANY,
                    "locked": False,
                    "team1": {
                        "code": "FI",
                        "description": "Finlande",
                        "flag": {"url": ANY},
                        "id": ANY,
                        "score": None,
                    },
                    "team2": {
                        "code": "NA",
                        "description": "Namibie",
                        "flag": {"url": ANY},
                        "id": ANY,
                        "score": None,
                    },
                },
            ],
        },
    }

    # Error case : bet by phase invalid code
    invalid_phase_code = "GR"

    response_by_phase_with_invalid_code = client.get(
        f"/api/v1/bets/phases/{invalid_phase_code}",
        headers={"Authorization": f"Bearer {authentication_token}"},
    )

    assert response_by_phase_with_invalid_code.json() == {
        "ok": False,
        "error_code": HTTPStatus.NOT_FOUND,
        "description": f"Phase not found: {invalid_phase_code}",
    }
