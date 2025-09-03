from http import HTTPStatus
from secrets import SystemRandom, randbelow
from typing import TYPE_CHECKING
from uuid import uuid4

import pendulum
from fastapi.testclient import TestClient

from testing.mock import MockLockDatetime, MockSettings
from testing.util import get_random_string
from yak_server.cli.database import initialize_database
from yak_server.helpers.settings import get_lock_datetime

if TYPE_CHECKING:
    import pytest
    from fastapi import FastAPI
    from sqlalchemy import Engine


def test_modify_score_bet(
    app_with_valid_jwt_config: "FastAPI",
    engine_for_test: "Engine",
    monkeypatch: "pytest.MonkeyPatch",
) -> None:
    monkeypatch.setattr(
        "yak_server.cli.database.get_settings",
        MockSettings(data_folder_relative="test_modify_bet_v2"),
    )

    initialize_database(engine_for_test, app_with_valid_jwt_config)

    user_name = get_random_string(10)
    first_name = get_random_string(5)
    last_name = get_random_string(8)
    password = get_random_string(15)

    client = TestClient(app_with_valid_jwt_config)

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

    response_get_all_bets = client.get(
        "/api/v1/bets",
        headers={"Authorization": f"Bearer {authentication_token}"},
    )

    assert response_get_all_bets.status_code == HTTPStatus.OK

    score_bet_ids = [
        score_bet["id"] for score_bet in response_get_all_bets.json()["result"]["score_bets"]
    ]

    # Success case : check update is OK
    score1 = 4
    score2 = 4

    response_patch_one_bet = client.patch(
        f"/api/v1/score_bets/{score_bet_ids[0]}",
        json={"team1": {"score": score1}, "team2": {"score": score2}},
        headers={"Authorization": f"Bearer {authentication_token}"},
    )

    assert response_patch_one_bet.status_code == HTTPStatus.OK
    assert response_patch_one_bet.json()["result"]["score_bet"]["team1"]["score"] == score1
    assert response_patch_one_bet.json()["result"]["score_bet"]["team2"]["score"] == score2

    # Success case : check no updates
    response_patch_no_updates = client.patch(
        f"/api/v1/score_bets/{score_bet_ids[0]}",
        json={"team1": {"score": score1}, "team2": {"score": score2}},
        headers={"Authorization": f"Bearer {authentication_token}"},
    )

    assert response_patch_no_updates.status_code == HTTPStatus.OK
    assert response_patch_no_updates.json()["result"]["score_bet"]["team1"]["score"] == score1
    assert response_patch_no_updates.json()["result"]["score_bet"]["team2"]["score"] == score2

    # Error case : check locked bet
    app_with_valid_jwt_config.dependency_overrides[get_lock_datetime] = MockLockDatetime(
        pendulum.now("UTC") - pendulum.duration(minutes=10),
    )

    response_locked_bet = client.patch(
        f"/api/v1/score_bets/{score_bet_ids[0]}",
        json={"team1": {"score": score1}, "team2": {"score": score2}},
        headers={"Authorization": f"Bearer {authentication_token}"},
    )

    assert response_locked_bet.json() == {
        "ok": False,
        "error_code": HTTPStatus.UNAUTHORIZED,
        "description": "Cannot modify score bet, lock date is exceeded",
    }

    app_with_valid_jwt_config.dependency_overrides[get_lock_datetime] = MockLockDatetime(
        pendulum.now("UTC") + pendulum.duration(minutes=10),
    )

    # Error case : check bet not found
    non_existing_bet_id = uuid4()

    response_bet_not_found = client.patch(
        f"/api/v1/score_bets/{non_existing_bet_id}",
        json={"team1": {"score": score1}, "team2": {"score": score2}},
        headers={"Authorization": f"Bearer {authentication_token}"},
    )

    assert response_bet_not_found.json() == {
        "ok": False,
        "error_code": HTTPStatus.NOT_FOUND,
        "description": f"Bet not found: {non_existing_bet_id}",
    }

    # Error case : check new score negative error
    response_new_score_negative = client.patch(
        f"/api/v1/score_bets/{score_bet_ids[0]}",
        json={"team1": {"score": -1}, "team2": {"score": score2}},
        headers={"Authorization": f"Bearer {authentication_token}"},
    )

    assert response_new_score_negative.json() == {
        "ok": False,
        "error_code": HTTPStatus.UNPROCESSABLE_ENTITY,
        "description": [
            {
                "error": "Input should be greater than or equal to 0",
                "field": "body -> team1 -> score",
            },
        ],
    }

    # Patch second bet
    secret_rng = SystemRandom()

    response_patch_second_bet = client.patch(
        f"/api/v1/score_bets/{score_bet_ids[1]}",
        json={"team1": {"score": randbelow(5)}, "team2": {"score": secret_rng.randrange(1, 3)}},
        headers={"Authorization": f"Bearer {authentication_token}"},
    )

    assert response_patch_second_bet.status_code == HTTPStatus.OK

    # Patch third bet
    response_patch_third_bet = client.patch(
        f"/api/v1/score_bets/{score_bet_ids[2]}",
        json={"team1": {"score": randbelow(3)}, "team2": {"score": secret_rng.randrange(2, 3)}},
        headers={"Authorization": f"Bearer {authentication_token}"},
    )

    assert response_patch_third_bet.status_code == HTTPStatus.OK
