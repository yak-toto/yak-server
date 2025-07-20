from copy import copy
from http import HTTPStatus
from secrets import SystemRandom, randbelow
from typing import TYPE_CHECKING, Any

from starlette.testclient import TestClient

from testing.mock import MockSettings
from testing.util import get_random_string
from yak_server.cli.database import initialize_database

if TYPE_CHECKING:
    import pytest
    from fastapi import FastAPI
    from sqlalchemy import Engine


def test_group_rank_and_modify_score_bet(
    app_with_valid_jwt_config: "FastAPI",
    engine_for_test: "Engine",
    monkeypatch: "pytest.MonkeyPatch",
) -> None:
    monkeypatch.setattr(
        "yak_server.cli.database.get_settings",
        MockSettings(data_folder_relative="test_modify_bet_v2"),
    )

    initialize_database(engine_for_test, app_with_valid_jwt_config)

    client = TestClient(app_with_valid_jwt_config)

    # Signup user
    response_signup = client.post(
        "/api/v1/users/signup",
        json={
            "name": get_random_string(6),
            "first_name": get_random_string(10),
            "last_name": get_random_string(10),
            "password": get_random_string(12),
        },
    )

    assert response_signup.status_code == HTTPStatus.CREATED

    authentication_token = response_signup.json()["result"]["access_token"]

    # Retrieve all the bets
    response_all_bets = client.get(
        "/api/v1/bets",
        headers={"Authorization": f"Bearer {authentication_token}"},
    )

    assert response_all_bets.status_code == HTTPStatus.OK

    # Perform PATCH bets
    bet_ids = [score_bet["id"] for score_bet in response_all_bets.json()["result"]["score_bets"]]
    SystemRandom().shuffle(bet_ids)

    for bet_id in bet_ids:
        score1 = randbelow(5)
        score2 = randbelow(5)

        response = client.patch(
            f"/api/v1/score_bets/{bet_id}",
            json={"team1": {"score": score1}, "team2": {"score": score2}},
            headers={"Authorization": f"Bearer {authentication_token}"},
            follow_redirects=True,
        )
        assert response.status_code == HTTPStatus.OK
        assert response.json()["result"]["score_bet"]["id"] == bet_id
        assert response.json()["result"]["score_bet"]["team1"]["score"] == score1
        assert response.json()["result"]["score_bet"]["team2"]["score"] == score2

    # Retrieve group rank
    response_group_rank = client.get(
        "/api/v1/bets/groups/rank/A",
        headers={"Authorization": f"Bearer {authentication_token}"},
    )

    assert response_group_rank.status_code == HTTPStatus.OK

    group_rank = response_group_rank.json()["result"]["group_rank"]

    response_group_by_bet = client.get(
        "/api/v1/bets/groups/A",
        headers={"Authorization": f"Bearer {authentication_token}"},
    )

    score_bets = response_group_by_bet.json()["result"]["score_bets"]

    teams: dict[str, Any] = {}

    default_config = {
        "won": 0,
        "drawn": 0,
        "lost": 0,
        "goals_for": 0,
        "goals_against": 0,
        "points": 0,
    }

    for score_bet in score_bets:
        team1_id = score_bet["team1"]["id"]
        team2_id = score_bet["team2"]["id"]

        if team1_id not in teams:
            teams[team1_id] = copy(default_config)
            teams[team1_id]["team"] = {
                key: value for key, value in score_bet["team1"].items() if key != "score"
            }

        if team2_id not in teams:
            teams[team2_id] = copy(default_config)
            teams[team2_id]["team"] = {
                key: value for key, value in score_bet["team2"].items() if key != "score"
            }

        teams[team1_id]["goals_for"] += score_bet["team1"]["score"]
        teams[team1_id]["goals_against"] += score_bet["team2"]["score"]
        teams[team2_id]["goals_for"] += score_bet["team2"]["score"]
        teams[team2_id]["goals_against"] += score_bet["team1"]["score"]

        if score_bet["team1"]["score"] > score_bet["team2"]["score"]:
            teams[team1_id]["won"] += 1
            teams[team2_id]["lost"] += 1
        elif score_bet["team1"]["score"] == score_bet["team2"]["score"]:
            teams[team1_id]["drawn"] += 1
            teams[team2_id]["drawn"] += 1
        else:
            teams[team1_id]["lost"] += 1
            teams[team2_id]["won"] += 1

    for team in teams.values():
        team["played"] = team["won"] + team["drawn"] + team["lost"]
        team["goals_difference"] = team["goals_for"] - team["goals_against"]
        team["points"] = 3 * team["won"] + team["drawn"]

    assert sorted(group_rank, key=lambda group_position: group_position["team"]["id"]) == sorted(
        teams.values(),
        key=lambda group_position: group_position["team"]["id"],
    )
