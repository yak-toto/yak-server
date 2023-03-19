import asyncio
from copy import copy
from datetime import datetime, timedelta
from http import HTTPStatus
from importlib import resources
from random import randint, shuffle

import pytest

from yak_server.cli.database import initialize_database

from .utils import get_random_string


@pytest.fixture(autouse=True)
def app_setup(app):
    testcase = "test_modify_bet_v2"

    # location of test data
    with resources.as_file(resources.files("tests") / testcase) as path:
        app.config["DATA_FOLDER"] = path
    old_lock_datetime = app.config["LOCK_DATETIME"]
    app.config["LOCK_DATETIME"] = str(datetime.now() + timedelta(minutes=10))

    with app.app_context():
        initialize_database(app)

    yield app

    app.config["LOCK_DATETIME"] = old_lock_datetime


@pytest.mark.asyncio()
async def test_spam_modify_score_bet(client, app_setup):
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

    authentification_token = response_signup.json["result"]["token"]

    # Retrieve all the bets
    response_all_bets = client.get(
        "/api/v1/bets",
        headers={"Authorization": f"Bearer {authentification_token}"},
    )

    assert response_all_bets.status_code == HTTPStatus.OK

    # Perform asynchronously 60 PATCH bets
    bet_ids = [score_bet["id"] for score_bet in response_all_bets.json["result"]["score_bets"]] * 10
    shuffle(bet_ids)

    scores = [(randint(0, 5), randint(0, 5)) for _ in range(len(bet_ids))]

    def send_async_request(client, bet_id, score1, score2, authentification_token):
        response = client.patch(
            f"/api/v1/score_bets/{bet_id}",
            json={"team1": {"score": score1}, "team2": {"score": score2}},
            headers={"Authorization": f"Bearer {authentification_token}"},
            follow_redirects=True,
        )
        assert response.status_code == HTTPStatus.OK
        assert response.json["result"]["score_bet"]["id"] == bet_id
        assert response.json["result"]["score_bet"]["team1"]["score"] == score1
        assert response.json["result"]["score_bet"]["team2"]["score"] == score2

    loop = asyncio.get_event_loop()
    futures = (
        loop.run_in_executor(
            None,
            send_async_request,
            client,
            bet_id,
            score[0],
            score[1],
            authentification_token,
        )
        for bet_id, score in zip(bet_ids, scores)
    )
    await asyncio.gather(*futures)

    # Retrieve group rank
    response_group_rank = client.get(
        "/api/v1/bets/groups/rank/A",
        headers={"Authorization": f"Bearer {authentification_token}"},
    )

    assert response_group_rank.status_code == HTTPStatus.OK

    group_rank = response_group_rank.json["result"]["group_rank"]

    response_group_by_bet = client.get(
        "/api/v1/bets/groups/A",
        headers={"Authorization": f"Bearer {authentification_token}"},
    )

    score_bets = response_group_by_bet.json["result"]["score_bets"]

    teams = {}

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
