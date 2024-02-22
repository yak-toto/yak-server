from http import HTTPStatus
from typing import TYPE_CHECKING
from uuid import uuid4

import pendulum
from starlette.testclient import TestClient

from testing.mock import MockSettings
from testing.util import get_random_string
from yak_server.cli.database import initialize_database
from yak_server.helpers.settings import get_settings

if TYPE_CHECKING:
    import pytest
    from fastapi import FastAPI


def test_modify_partial_score_bet(app: "FastAPI", monkeypatch: "pytest.MonkeyPatch") -> None:
    fake_jwt_secret_key = get_random_string(100)

    app.dependency_overrides[get_settings] = MockSettings(
        jwt_expiration_time=10,
        jwt_secret_key=fake_jwt_secret_key,
        lock_datetime_shift=pendulum.duration(minutes=10),
    )

    monkeypatch.setattr(
        "yak_server.cli.database.get_settings",
        MockSettings(data_folder_relative="test_modify_bet_v2"),
    )

    initialize_database(app)

    client = TestClient(app)

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
    authentication_token = response_signup.json()["result"]["token"]

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
