from http import HTTPStatus
from typing import TYPE_CHECKING
from uuid import uuid4

from starlette.testclient import TestClient

from testing.util import get_random_string, get_resources_path
from yak_server.cli.database import initialize_database

if TYPE_CHECKING:
    from fastapi import FastAPI
    from sqlalchemy import Engine


def test_modify_partial_score_bet(
    app_with_valid_jwt_config: "FastAPI", engine_for_test: "Engine"
) -> None:
    initialize_database(
        engine_for_test, app_with_valid_jwt_config, get_resources_path("test_modify_bet_v2")
    )

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

    response_get_all_bets = client.get(
        "/api/v1/bets",
        headers={"Authorization": f"Bearer {authentication_token}"},
    )

    assert response_get_all_bets.status_code == HTTPStatus.OK

    score_bet_ids = [
        score_bet["id"] for score_bet in response_get_all_bets.json()["result"]["score_bets"]
    ]

    # Success case : modify teams and scores
    score1 = 0
    score2 = 4

    new_team1 = response_get_all_bets.json()["result"]["score_bets"][-1]["team1"]
    new_team2 = response_get_all_bets.json()["result"]["score_bets"][-2]["team1"]

    response_patch_bet = client.patch(
        f"/api/v1/score_bets/{score_bet_ids[0]}",
        json={
            "team1": {"id": new_team1["id"], "score": score1},
            "team2": {"id": new_team2["id"], "score": score2},
        },
        headers={"Authorization": f"Bearer {authentication_token}"},
    )

    assert response_patch_bet.status_code == HTTPStatus.OK
    assert response_patch_bet.json()["result"]["score_bet"]["team1"] == {
        **new_team1,
        "score": score1,
    }
    assert response_patch_bet.json()["result"]["score_bet"]["team2"] == {
        **new_team2,
        "score": score2,
    }

    # Success case : Patch only the team1 id
    new_team1 = response_get_all_bets.json()["result"]["score_bets"][-3]["team1"]

    response_patch_only_team1_id = client.patch(
        f"/api/v1/score_bets/{score_bet_ids[0]}",
        json={"team1": {"id": new_team1["id"]}},
        headers={"Authorization": f"Bearer {authentication_token}"},
    )

    assert response_patch_only_team1_id.status_code == HTTPStatus.OK
    assert response_patch_only_team1_id.json()["result"]["score_bet"]["team1"] == {
        **new_team1,
        "score": score1,
    }

    # Success case : Patch only the team2 id
    new_team2 = response_get_all_bets.json()["result"]["score_bets"][-3]["team2"]

    response_patch_only_team2_id = client.patch(
        f"/api/v1/score_bets/{score_bet_ids[0]}",
        json={"team2": {"id": new_team2["id"]}},
        headers={"Authorization": f"Bearer {authentication_token}"},
    )

    assert response_patch_only_team2_id.status_code == HTTPStatus.OK
    assert response_patch_only_team2_id.json()["result"]["score_bet"]["team2"] == {
        **new_team2,
        "score": score2,
    }

    # Success case : no modification
    response_no_modification = client.patch(
        f"/api/v1/score_bets/{score_bet_ids[0]}",
        json={},
        headers={"Authorization": f"Bearer {authentication_token}"},
    )

    assert response_no_modification.status_code == HTTPStatus.OK
    assert response_no_modification.json() == response_patch_only_team2_id.json()

    # Error case : Patch team1 id with wrong non existing id
    wrong_team1_id = str(uuid4())

    response_patch_wrong_team1_id = client.patch(
        f"/api/v1/score_bets/{score_bet_ids[0]}",
        json={"team1": {"id": wrong_team1_id}},
        headers={"Authorization": f"Bearer {authentication_token}"},
    )

    assert response_patch_wrong_team1_id.status_code == HTTPStatus.NOT_FOUND
    assert response_patch_wrong_team1_id.json() == {
        "ok": False,
        "error_code": HTTPStatus.NOT_FOUND,
        "description": f"Team not found: {wrong_team1_id}",
    }

    # Error case : Patch team2 id with wrong non existing id
    wrong_team2_id = str(uuid4())

    response_patch_wrong_team2_id = client.patch(
        f"/api/v1/score_bets/{score_bet_ids[0]}",
        json={"team2": {"id": wrong_team2_id}},
        headers={"Authorization": f"Bearer {authentication_token}"},
    )

    assert response_patch_wrong_team2_id.status_code == HTTPStatus.NOT_FOUND
    assert response_patch_wrong_team2_id.json() == {
        "ok": False,
        "error_code": HTTPStatus.NOT_FOUND,
        "description": f"Team not found: {wrong_team2_id}",
    }
