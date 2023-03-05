from datetime import datetime, timedelta
from http import HTTPStatus
from random import randint
from uuid import uuid4

import pkg_resources

from yak_server.cli.database import initialize_database

from .test_utils import get_random_string


def test_modify_score_bet(app, client):
    testcase = "test_modify_bet_v2"

    # location of test data
    app.config["DATA_FOLDER"] = pkg_resources.resource_filename(__name__, testcase)
    app.config["LOCK_DATETIME"] = str(datetime.now() + timedelta(minutes=10))

    with app.app_context():
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
    authentification_token = response_signup.json["result"]["token"]

    response_get_all_bets = client.get(
        "/api/v1/bets",
        headers={"Authorization": f"Bearer {authentification_token}"},
    )

    assert response_get_all_bets.status_code == HTTPStatus.OK

    score_bet_ids = [
        score_bet["id"] for score_bet in response_get_all_bets.json["result"]["score_bets"]
    ]

    # Success case : check update is OK
    score1 = 4
    score2 = 4

    response_patch_one_bet = client.patch(
        f"/api/v1/bets/{score_bet_ids[0]}?type=score",
        json={"team1": {"score": score1}, "team2": {"score": score2}},
        headers={"Authorization": f"Bearer {authentification_token}"},
    )

    assert response_patch_one_bet.status_code == HTTPStatus.OK
    assert response_patch_one_bet.json["result"]["score_bet"]["team1"]["score"] == score1
    assert response_patch_one_bet.json["result"]["score_bet"]["team2"]["score"] == score2

    # Error case : check wrong inputs
    response_patch_wrong_inputs = client.patch(
        f"/api/v1/bets/{score_bet_ids[0]}?type=score",
        json={"team1": {}, "team2": {"score": score2}},
        headers={"Authorization": f"Bearer {authentification_token}"},
    )

    assert response_patch_wrong_inputs.json == {
        "ok": False,
        "error_code": HTTPStatus.UNAUTHORIZED,
        "description": "Wrong inputs",
    }

    # Error case : check locked bet
    app.config["LOCK_DATETIME"] = str(datetime.now() - timedelta(minutes=10))

    response_locked_bet = client.patch(
        f"/api/v1/bets/{score_bet_ids[0]}?type=score",
        json={"team1": {"score": score1}, "team2": {"score": score2}},
        headers={"Authorization": f"Bearer {authentification_token}"},
    )

    assert response_locked_bet.json == {
        "ok": False,
        "error_code": HTTPStatus.UNAUTHORIZED,
        "description": "Cannot modify bets because locked date is exceeded",
    }

    app.config["LOCK_DATETIME"] = str(datetime.now() + timedelta(minutes=10))

    # Error case : check invalid bet type
    response_invalid_bet_type = client.patch(
        f"/api/v1/bets/{score_bet_ids[0]}?type=scored",
        json={"team1": {"score": score1}, "team2": {"score": score2}},
        headers={"Authorization": f"Bearer {authentification_token}"},
    )

    assert response_invalid_bet_type.json == {
        "ok": False,
        "error_code": HTTPStatus.UNAUTHORIZED,
        "description": "Invalid bet type. The available bet types are : ('score', 'binary')",
    }

    # Error case : check bet not found
    non_existing_bet_id = str(uuid4())

    response_bet_not_found = client.patch(
        f"/api/v1/bets/{non_existing_bet_id}?type=score",
        json={"team1": {"score": score1}, "team2": {"score": score2}},
        headers={"Authorization": f"Bearer {authentification_token}"},
    )

    assert response_bet_not_found.json == {
        "ok": False,
        "error_code": HTTPStatus.NOT_FOUND,
        "description": f"Bet not found: {non_existing_bet_id}",
    }

    # Error case : check new score negative error
    response_new_score_negative = client.patch(
        f"/api/v1/bets/{score_bet_ids[0]}?type=score",
        json={"team1": {"score": -1}, "team2": {"score": score2}},
        headers={"Authorization": f"Bearer {authentification_token}"},
    )

    assert response_new_score_negative.json == {
        "ok": False,
        "error_code": HTTPStatus.UNAUTHORIZED,
        "description": "Score cannot be negative",
    }

    # Patch second bet
    response_patch_second_bet = client.patch(
        f"/api/v1/bets/{score_bet_ids[1]}?type=score",
        json={"team1": {"score": randint(0, 5)}, "team2": {"score": randint(1, 3)}},
        headers={"Authorization": f"Bearer {authentification_token}"},
    )

    assert response_patch_second_bet.status_code == HTTPStatus.OK

    # Patch third bet
    response_patch_third_bet = client.patch(
        f"/api/v1/bets/{score_bet_ids[2]}?type=score",
        json={"team1": {"score": randint(0, 3)}, "team2": {"score": randint(2, 3)}},
        headers={"Authorization": f"Bearer {authentification_token}"},
    )

    assert response_patch_third_bet.status_code == HTTPStatus.OK
