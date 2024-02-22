from http import HTTPStatus
from typing import TYPE_CHECKING

import pendulum

from testing.mock import MockSettings
from testing.util import get_random_string
from yak_server.cli.database import initialize_database
from yak_server.helpers.settings import get_settings

if TYPE_CHECKING:
    import pytest
    from fastapi import FastAPI
    from starlette.testclient import TestClient


def test_delete_score_bet(
    app: "FastAPI",
    client: "TestClient",
    monkeypatch: "pytest.MonkeyPatch",
) -> None:
    fake_jwt_secret_key = get_random_string(100)

    app.dependency_overrides[get_settings] = MockSettings(
        jwt_secret_key=fake_jwt_secret_key,
        jwt_expiration_time=10,
        lock_datetime_shift=pendulum.duration(minutes=10),
    )

    monkeypatch.setattr(
        "yak_server.cli.database.get_settings",
        MockSettings(data_folder_relative="test_modify_bet_v2"),
    )

    initialize_database(app)

    # Signup one user
    response_signup = client.post(
        "/api/v1/users/signup",
        json={
            "name": get_random_string(6),
            "first_name": get_random_string(6),
            "last_name": get_random_string(6),
            "password": get_random_string(49),
        },
    )

    assert response_signup.status_code == HTTPStatus.CREATED

    # Fetch all bets and get the ids
    token = response_signup.json()["result"]["token"]

    response_all_bets = client.get("/api/v1/bets", headers={"Authorization": f"Bearer {token}"})

    assert response_all_bets.status_code == HTTPStatus.OK

    bet_id = response_all_bets.json()["result"]["score_bets"][0]["id"]

    # Retrieve one score bet
    response_get_score_bet = client.get(
        f"/api/v1/score_bets/{bet_id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response_get_score_bet.status_code == HTTPStatus.OK

    # Delete one score bet and compare it to the GET response
    response_delete_score_bet = client.delete(
        f"/api/v1/score_bets/{bet_id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response_delete_score_bet.status_code == HTTPStatus.OK
    assert response_delete_score_bet.json() == response_get_score_bet.json()

    # Try to delete a second times and error
    response_delete_score_bet_second_times = client.delete(
        f"/api/v1/score_bets/{bet_id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response_delete_score_bet_second_times.status_code == HTTPStatus.NOT_FOUND
    assert response_delete_score_bet_second_times.json() == {
        "ok": False,
        "error_code": HTTPStatus.NOT_FOUND,
        "description": f"Bet not found: {bet_id}",
    }

    # Check bet locking
    app.dependency_overrides[get_settings] = MockSettings(
        lock_datetime_shift=-pendulum.duration(minutes=10),
        jwt_expiration_time=10,
        jwt_secret_key=fake_jwt_secret_key,
    )

    bet2_id = response_all_bets.json()["result"]["score_bets"][1]["id"]

    response_delete_locked_score_bet = client.delete(
        f"/api/v1/score_bets/{bet2_id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response_delete_locked_score_bet.status_code == HTTPStatus.UNAUTHORIZED
    assert response_delete_locked_score_bet.json() == {
        "ok": False,
        "error_code": HTTPStatus.UNAUTHORIZED,
        "description": "Cannot modify score bet, lock date is exceeded",
    }
