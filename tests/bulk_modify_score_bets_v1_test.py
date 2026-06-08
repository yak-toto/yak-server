from datetime import datetime, timedelta, timezone
from http import HTTPStatus
from typing import TYPE_CHECKING
from uuid import uuid4

from fastapi.testclient import TestClient

from testing.mock import MockLockDatetime
from testing.util import get_random_string, get_resources_path
from yak_server.cli.database import initialize_database
from yak_server.helpers.settings import get_lock_datetime

if TYPE_CHECKING:
    from fastapi import FastAPI
    from sqlalchemy import Engine


def test_bulk_modify_score_bets(
    app_with_valid_jwt_config: "FastAPI", engine_for_test: "Engine"
) -> None:
    initialize_database(engine_for_test, get_resources_path("test_modify_bet_v2"))

    client = TestClient(app_with_valid_jwt_config)

    response_signup = client.post(
        "/api/v1/users/signup",
        json={
            "name": get_random_string(10),
            "first_name": get_random_string(5),
            "last_name": get_random_string(8),
            "password": get_random_string(15),
        },
    )

    assert response_signup.status_code == HTTPStatus.CREATED
    authentication_token = response_signup.json()["result"]["access_token"]
    headers = {"Authorization": f"Bearer {authentication_token}"}

    response_get_all_bets = client.get("/api/v1/bets", headers=headers)
    assert response_get_all_bets.status_code == HTTPStatus.OK

    score_bet_ids = [
        score_bet["id"] for score_bet in response_get_all_bets.json()["result"]["score_bets"]
    ]

    # Success case: bulk update all bets in one request
    payload = [
        {"id": score_bet_ids[0], "team1": {"score": 2}, "team2": {"score": 1}},
        {"id": score_bet_ids[1], "team1": {"score": 0}, "team2": {"score": 0}},
        {"id": score_bet_ids[2], "team1": {"score": 3}, "team2": {"score": 2}},
    ]

    response_bulk = client.patch("/api/v1/score_bets", json=payload, headers=headers)

    assert response_bulk.status_code == HTTPStatus.OK
    results = response_bulk.json()["result"]
    assert len(results) == 3
    assert results[0]["score_bet"]["team1"]["score"] == 2
    assert results[0]["score_bet"]["team2"]["score"] == 1
    assert results[1]["score_bet"]["team1"]["score"] == 0
    assert results[1]["score_bet"]["team2"]["score"] == 0
    assert results[2]["score_bet"]["team1"]["score"] == 3
    assert results[2]["score_bet"]["team2"]["score"] == 2

    # Success case: response order matches request order
    payload_reversed = [
        {"id": score_bet_ids[2], "team1": {"score": 1}, "team2": {"score": 1}},
        {"id": score_bet_ids[0], "team1": {"score": 4}, "team2": {"score": 0}},
    ]

    response_reversed = client.patch("/api/v1/score_bets", json=payload_reversed, headers=headers)

    assert response_reversed.status_code == HTTPStatus.OK
    results_reversed = response_reversed.json()["result"]
    assert results_reversed[0]["score_bet"]["id"] == score_bet_ids[2]
    assert results_reversed[1]["score_bet"]["id"] == score_bet_ids[0]

    # Error case: locked bets
    app_with_valid_jwt_config.dependency_overrides[get_lock_datetime] = MockLockDatetime(
        datetime.now(timezone.utc) - timedelta(minutes=10),
    )

    response_locked = client.patch("/api/v1/score_bets", json=payload, headers=headers)

    assert response_locked.json() == {
        "ok": False,
        "error_code": "locked_score_bet",
        "description": "Cannot modify score bet, lock date is exceeded",
    }

    app_with_valid_jwt_config.dependency_overrides[get_lock_datetime] = MockLockDatetime(
        datetime.now(timezone.utc) + timedelta(minutes=10),
    )

    # Error case: one unknown bet id in the list
    unknown_id = uuid4()

    response_not_found = client.patch(
        "/api/v1/score_bets",
        json=[{"id": str(unknown_id), "team1": {"score": 1}, "team2": {"score": 0}}],
        headers=headers,
    )

    assert response_not_found.json() == {
        "ok": False,
        "error_code": "bet_not_found",
        "description": f"Bet not found: {unknown_id}",
    }

    # Error case: negative score
    response_negative_score = client.patch(
        "/api/v1/score_bets",
        json=[{"id": score_bet_ids[0], "team1": {"score": -1}, "team2": {"score": 0}}],
        headers=headers,
    )

    assert response_negative_score.json() == {
        "ok": False,
        "error_code": "validation_error",
        "description": [
            {
                "error": "Input should be greater than or equal to 0",
                "field": "body -> 0 -> team1 -> score",
            },
        ],
    }
