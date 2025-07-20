from http import HTTPStatus
from typing import TYPE_CHECKING

import pendulum
from starlette.testclient import TestClient

from testing.mock import MockSettings
from testing.util import get_random_string
from yak_server.cli.database import initialize_database
from yak_server.helpers.settings import get_settings

if TYPE_CHECKING:
    import pytest
    from fastapi import FastAPI
    from sqlalchemy import Engine


def test_delete_binary_bet(
    app_with_valid_jwt_config: "FastAPI",
    engine_for_test: "Engine",
    monkeypatch: "pytest.MonkeyPatch",
) -> None:
    monkeypatch.setattr(
        "yak_server.cli.database.get_settings",
        MockSettings(data_folder_relative="test_binary_bet"),
    )

    initialize_database(engine_for_test, app_with_valid_jwt_config)

    client = TestClient(app_with_valid_jwt_config)

    # Signup one user
    response_signup = client.post(
        "/api/v1/users/signup",
        json={
            "name": get_random_string(6),
            "first_name": get_random_string(6),
            "last_name": get_random_string(6),
            "password": get_random_string(16),
        },
    )

    assert response_signup.status_code == HTTPStatus.CREATED

    # Fetch all bets and get the binary bet id
    access_token = response_signup.json()["result"]["access_token"]

    response_all_bets = client.get(
        "/api/v1/bets", headers={"Authorization": f"Bearer {access_token}"}
    )

    assert response_all_bets.status_code == HTTPStatus.OK

    binary_bet_id = response_all_bets.json()["result"]["binary_bets"][0]["id"]

    # Check bet locking
    app_with_valid_jwt_config.dependency_overrides[get_settings]().set_lock_datetime(
        -pendulum.duration(minutes=10)
    )

    response_delete_locked_binary_bet = client.delete(
        f"/api/v1/binary_bets/{binary_bet_id}",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert response_delete_locked_binary_bet.status_code == HTTPStatus.UNAUTHORIZED
    assert response_delete_locked_binary_bet.json() == {
        "ok": False,
        "error_code": HTTPStatus.UNAUTHORIZED,
        "description": "Cannot modify binary bet, lock date is exceeded",
    }

    app_with_valid_jwt_config.dependency_overrides[get_settings]().set_lock_datetime(
        pendulum.duration(minutes=10)
    )

    # Retrieve one binary bet
    response_get_binary_bet = client.get(
        f"/api/v1/binary_bets/{binary_bet_id}",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert response_get_binary_bet.status_code == HTTPStatus.OK

    # Delete one binary bet and compare it to the GET response
    response_delete_binary_bet = client.delete(
        f"/api/v1/binary_bets/{binary_bet_id}",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert response_delete_binary_bet.status_code == HTTPStatus.OK
    assert response_delete_binary_bet.json() == response_get_binary_bet.json()

    # Try to delete a second times and error
    response_delete_binary_bet_second_times = client.delete(
        f"/api/v1/binary_bets/{binary_bet_id}",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert response_delete_binary_bet_second_times.status_code == HTTPStatus.NOT_FOUND
    assert response_delete_binary_bet_second_times.json() == {
        "ok": False,
        "error_code": HTTPStatus.NOT_FOUND,
        "description": f"Bet not found: {binary_bet_id}",
    }
