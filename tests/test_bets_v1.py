from http import HTTPStatus
from importlib import resources
from unittest.mock import ANY
from uuid import uuid4

import pytest

from yak_server.cli.database import initialize_database

from .utils import get_random_string


@pytest.fixture(autouse=True)
def setup_app(app):
    testcase = "test_modify_bet_v2"

    with resources.as_file(resources.files("tests") / testcase) as path:
        app.config["DATA_FOLDER"] = path

    with app.app_context():
        initialize_database(app)

    return app


def test_bets(client):
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
    authentification_token = response_signup.json["result"]["token"]

    # Get all bets to retrieve ids
    response_get_all_bets = client.get(
        "/api/v1/bets",
        headers={"Authorization": f"Bearer {authentification_token}"},
    )

    assert response_get_all_bets.status_code == HTTPStatus.OK

    score_bet_ids = [
        score_bet["id"] for score_bet in response_get_all_bets.json["result"]["score_bets"]
    ]

    # Success case : check get one bet
    response_bet_by_id = client.get(
        f"/api/v1/score_bets/{score_bet_ids[0]}",
        headers={"Authorization": f"Bearer {authentification_token}"},
    )

    assert response_bet_by_id.status_code == HTTPStatus.OK
    assert response_bet_by_id.json == {
        "ok": True,
        "result": {
            "group": {
                "code": "A",
                "description": "Groupe A",
                "id": ANY,
            },
            "phase": {
                "code": "GROUP",
                "description": "Group stage",
                "id": ANY,
            },
            "score_bet": {
                "id": ANY,
                "index": 1,
                "locked": True,
                "team1": {
                    "code": "HR",
                    "description": "Crotia",
                    "flag": {"url": ANY},
                    "id": ANY,
                    "score": None,
                },
                "team2": {
                    "code": "FI",
                    "description": "Finland",
                    "flag": {"url": ANY},
                    "id": ANY,
                    "score": None,
                },
            },
        },
    }

    # Error case : bet with invalid id
    invalid_bet_id = str(uuid4())

    response_bet_with_invalid_id = client.get(
        f"/api/v1/score_bets/{invalid_bet_id}",
        headers={"Authorization": f"Bearer {authentification_token}"},
    )

    assert response_bet_with_invalid_id.status_code == HTTPStatus.NOT_FOUND
    assert response_bet_with_invalid_id.json == {
        "ok": False,
        "error_code": HTTPStatus.NOT_FOUND,
        "description": f"Bet not found: {invalid_bet_id}",
    }

    # Success case : bet by phase
    response_by_phase = client.get(
        "/api/v1/bets/phases/GROUP",
        headers={"Authorization": f"Bearer {authentification_token}"},
    )

    assert response_by_phase.status_code == HTTPStatus.OK
    assert response_by_phase.json == {
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
                "description": "Group stage",
                "id": ANY,
            },
            "score_bets": [
                {
                    "group": {"id": ANY},
                    "id": ANY,
                    "index": 1,
                    "locked": True,
                    "team1": {
                        "code": "HR",
                        "description": "Crotia",
                        "flag": {"url": ANY},
                        "id": ANY,
                        "score": None,
                    },
                    "team2": {
                        "code": "FI",
                        "description": "Finland",
                        "flag": {"url": ANY},
                        "id": ANY,
                        "score": None,
                    },
                },
                {
                    "group": {"id": ANY},
                    "id": ANY,
                    "index": 2,
                    "locked": True,
                    "team1": {
                        "code": "NA",
                        "description": "Namibia",
                        "flag": {"url": ANY},
                        "id": ANY,
                        "score": None,
                    },
                    "team2": {
                        "code": "IQ",
                        "description": "Iraq",
                        "flag": {"url": ANY},
                        "id": ANY,
                        "score": None,
                    },
                },
                {
                    "group": {"id": ANY},
                    "id": ANY,
                    "index": 3,
                    "locked": True,
                    "team1": {
                        "code": "HR",
                        "description": "Crotia",
                        "flag": {"url": ANY},
                        "id": ANY,
                        "score": None,
                    },
                    "team2": {
                        "code": "NA",
                        "description": "Namibia",
                        "flag": {"url": ANY},
                        "id": ANY,
                        "score": None,
                    },
                },
                {
                    "group": {"id": ANY},
                    "id": ANY,
                    "index": 4,
                    "locked": True,
                    "team1": {
                        "code": "FI",
                        "description": "Finland",
                        "flag": {"url": ANY},
                        "id": ANY,
                        "score": None,
                    },
                    "team2": {
                        "code": "IQ",
                        "description": "Iraq",
                        "flag": {"url": ANY},
                        "id": ANY,
                        "score": None,
                    },
                },
                {
                    "group": {"id": ANY},
                    "id": ANY,
                    "index": 5,
                    "locked": True,
                    "team1": {
                        "code": "HR",
                        "description": "Crotia",
                        "flag": {"url": ANY},
                        "id": ANY,
                        "score": None,
                    },
                    "team2": {
                        "code": "IQ",
                        "description": "Iraq",
                        "flag": {"url": ANY},
                        "id": ANY,
                        "score": None,
                    },
                },
                {
                    "group": {"id": ANY},
                    "id": ANY,
                    "index": 6,
                    "locked": True,
                    "team1": {
                        "code": "FI",
                        "description": "Finland",
                        "flag": {"url": ANY},
                        "id": ANY,
                        "score": None,
                    },
                    "team2": {
                        "code": "NA",
                        "description": "Namibia",
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
        headers={"Authorization": f"Bearer {authentification_token}"},
    )

    assert response_by_phase_with_invalid_code.json == {
        "ok": False,
        "error_code": HTTPStatus.NOT_FOUND,
        "description": f"Phase not found: {invalid_phase_code}",
    }
