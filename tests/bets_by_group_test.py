from http import HTTPStatus
from typing import TYPE_CHECKING
from unittest.mock import ANY

from starlette.testclient import TestClient

from testing.mock import MockSettings
from testing.util import get_random_string
from yak_server.cli.database import initialize_database

if TYPE_CHECKING:
    import pytest
    from fastapi import FastAPI
    from sqlalchemy import Engine


def test_bets_by_groups(
    app_with_valid_jwt_config: "FastAPI",
    engine_for_test: "Engine",
    monkeypatch: "pytest.MonkeyPatch",
) -> None:
    client = TestClient(app_with_valid_jwt_config)

    monkeypatch.setattr(
        "yak_server.cli.database.get_settings",
        MockSettings(data_folder_relative="test_compute_points_v1"),
    )

    initialize_database(engine_for_test, app_with_valid_jwt_config)

    response_signup = client.post(
        "/api/v1/users/signup",
        json={
            "name": get_random_string(6),
            "first_name": get_random_string(6),
            "last_name": get_random_string(6),
            "password": get_random_string(9),
        },
    )

    assert response_signup.status_code == HTTPStatus.CREATED

    access_token = response_signup.json()["result"]["access_token"]

    # Success case
    bets_by_valid_group = client.get(
        "/api/v1/bets/groups/A",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert bets_by_valid_group.json()["result"] == {
        "binary_bets": [
            {
                "id": ANY,
                "locked": False,
                "team1": None,
                "team2": None,
            },
        ],
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
        "score_bets": [
            {
                "id": ANY,
                "locked": False,
                "team1": {
                    "code": "FR",
                    "description": "France",
                    "flag": {"url": ANY},
                    "id": ANY,
                    "score": None,
                },
                "team2": {
                    "code": "IE",
                    "description": "Irlande",
                    "flag": {"url": ANY},
                    "id": ANY,
                    "score": None,
                },
            },
            {
                "id": ANY,
                "locked": False,
                "team1": {
                    "code": "FR",
                    "description": "France",
                    "flag": {"url": ANY},
                    "id": ANY,
                    "score": None,
                },
                "team2": {
                    "code": "IM",
                    "description": "Île de Man",
                    "flag": {"url": ANY},
                    "id": ANY,
                    "score": None,
                },
            },
            {
                "id": ANY,
                "locked": False,
                "team1": {
                    "code": "IE",
                    "description": "Irlande",
                    "flag": {"url": ANY},
                    "id": ANY,
                    "score": None,
                },
                "team2": {
                    "code": "IM",
                    "description": "Île de Man",
                    "flag": {"url": ANY},
                    "id": ANY,
                    "score": None,
                },
            },
        ],
    }

    for score_bet in bets_by_valid_group.json()["result"]["score_bets"]:
        assert score_bet["team1"]["flag"]["url"] == f"/api/v1/teams/{score_bet['team1']['id']}/flag"
        assert score_bet["team2"]["flag"]["url"] == f"/api/v1/teams/{score_bet['team2']['id']}/flag"

    # Error case : invalid group code
    invalid_group_code = "B"

    bets_by_invalid_group_code = client.get(
        f"/api/v1/bets/groups/{invalid_group_code}",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert bets_by_invalid_group_code.json() == {
        "ok": False,
        "error_code": HTTPStatus.NOT_FOUND,
        "description": f"Group not found: {invalid_group_code}",
    }
