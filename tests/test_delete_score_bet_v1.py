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
    with resources.as_file(resources.files("tests") / "test_data/test_modify_bet_v2") as path:
        app.config["DATA_FOLDER"] = path
    old_lock_datetime = app.config["LOCK_DATETIME"]
    app.config["LOCK_DATETIME"] = str(get_paris_datetime_now() + timedelta(minutes=10))

    with app.app_context():
        initialize_database(app)

    yield app

    app.config["LOCK_DATETIME"] = old_lock_datetime


def test_delete_score_bet(client, setup_app):
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

    # Fetch all bets and get the ids
    token = response_signup.json["result"]["token"]

    response_all_bets = client.get("/api/v1/bets", headers={"Authorization": f"Bearer {token}"})

    assert response_all_bets.status_code == HTTPStatus.OK

    bet_id = response_all_bets.json["result"]["score_bets"][0]["id"]

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
    assert response_delete_score_bet.json == response_get_score_bet.json

    # Try to delete a second times and error
    response_delete_score_bet_second_times = client.delete(
        f"/api/v1/score_bets/{bet_id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response_delete_score_bet_second_times.status_code == HTTPStatus.NOT_FOUND
    assert response_delete_score_bet_second_times.json == {
        "ok": False,
        "error_code": HTTPStatus.NOT_FOUND,
        "description": f"Bet not found: {bet_id}",
    }

    # Check bet locking
    old_lock_datetime = setup_app.config["LOCK_DATETIME"]
    setup_app.config["LOCK_DATETIME"] = str(get_paris_datetime_now() - timedelta(minutes=10))

    bet2_id = response_all_bets.json["result"]["score_bets"][1]["id"]

    response_delete_locked_score_bet = client.delete(
        f"/api/v1/score_bets/{bet2_id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response_delete_locked_score_bet.status_code == HTTPStatus.UNAUTHORIZED
    assert response_delete_locked_score_bet.json == {
        "ok": False,
        "error_code": HTTPStatus.UNAUTHORIZED,
        "description": "Cannot modify score bet, lock date is exceeded",
    }

    setup_app.config["LOCK_DATETIME"] = old_lock_datetime
