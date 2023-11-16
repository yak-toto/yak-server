from http import HTTPStatus
from typing import TYPE_CHECKING
from unittest.mock import ANY
from uuid import uuid4

import pendulum

from yak_server.cli.database import initialize_database
from yak_server.helpers.settings import get_settings

from .utils import get_random_string
from .utils.mock import MockSettings

if TYPE_CHECKING:
    import pytest
    from fastapi import FastAPI
    from starlette.testclient import TestClient


def test_bets(app: "FastAPI", client: "TestClient", monkeypatch: "pytest.MonkeyPatch") -> None:
    fake_jwt_secret_key = get_random_string(100)

    app.dependency_overrides[get_settings] = MockSettings(
        jwt_expiration_time=10,
        jwt_secret_key=fake_jwt_secret_key,
        lock_datetime_shift=-pendulum.duration(minutes=10),
    )

    monkeypatch.setattr(
        "yak_server.cli.database.get_settings",
        MockSettings(data_folder_relative="test_modify_bet_v2"),
    )

    initialize_database(app)

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
    authentication_token = response_signup.json()["result"]["token"]

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
                "locked": True,
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
                    "locked": True,
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
                    "locked": True,
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
                    "locked": True,
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
                    "locked": True,
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
                    "locked": True,
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
                    "locked": True,
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
