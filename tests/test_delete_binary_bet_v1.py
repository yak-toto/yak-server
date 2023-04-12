import sys
from datetime import timedelta
from http import HTTPStatus

if sys.version_info >= (3, 9):
    from importlib import resources
else:
    import importlib_resources as resources

import pytest

from yak_server.cli.database import initialize_database

from .utils import get_paris_datetime_now, get_random_string


@pytest.fixture()
def setup_app(app):
    # location of test data
    with resources.as_file(resources.files("tests") / "test_data/test_binary_bet") as path:
        app.config["DATA_FOLDER"] = path
    old_lock_datetime = app.config["LOCK_DATETIME"]
    app.config["LOCK_DATETIME"] = str(get_paris_datetime_now() + timedelta(minutes=10))

    with app.app_context():
        initialize_database(app)

    yield app

    app.config["LOCK_DATETIME"] = old_lock_datetime


def test_delete_binary_bet(client, setup_app):
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

    # Fetch all bets and get the binary bet id
    token = response_signup.json["result"]["token"]

    response_all_bets = client.get("/api/v1/bets", headers={"Authorization": f"Bearer {token}"})

    assert response_all_bets.status_code == HTTPStatus.OK

    binary_bet_id = response_all_bets.json["result"]["binary_bets"][0]["id"]

    # Check bet locking
    old_lock_datetime = setup_app.config["LOCK_DATETIME"]
    setup_app.config["LOCK_DATETIME"] = str(get_paris_datetime_now() - timedelta(minutes=10))

    response_delete_locked_binary_bet = client.delete(
        f"/api/v1/binary_bets/{binary_bet_id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response_delete_locked_binary_bet.status_code == HTTPStatus.UNAUTHORIZED
    assert response_delete_locked_binary_bet.json == {
        "ok": False,
        "error_code": HTTPStatus.UNAUTHORIZED,
        "description": "Cannot modify binary bet, lock date is exceeded",
    }

    setup_app.config["LOCK_DATETIME"] = old_lock_datetime

    # Retrieve one binary bet
    response_get_binary_bet = client.get(
        f"/api/v1/binary_bets/{binary_bet_id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response_get_binary_bet.status_code == HTTPStatus.OK

    # Delete one binary bet and compare it to the GET response
    response_delete_binary_bet = client.delete(
        f"/api/v1/binary_bets/{binary_bet_id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response_delete_binary_bet.status_code == HTTPStatus.OK
    assert response_delete_binary_bet.json == response_get_binary_bet.json

    # Try to delete a second times and error
    response_delete_binary_bet_second_times = client.delete(
        f"/api/v1/binary_bets/{binary_bet_id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response_delete_binary_bet_second_times.status_code == HTTPStatus.NOT_FOUND
    assert response_delete_binary_bet_second_times.json == {
        "ok": False,
        "error_code": HTTPStatus.NOT_FOUND,
        "description": f"Bet not found: {binary_bet_id}",
    }
