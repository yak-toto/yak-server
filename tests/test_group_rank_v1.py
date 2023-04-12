import sys
from datetime import timedelta
from http import HTTPStatus

if sys.version_info >= (3, 9):
    from importlib import resources
else:
    import importlib_resources as resources

from unittest.mock import ANY

import pytest

from yak_server.cli.database import initialize_database

from .utils import get_paris_datetime_now, get_random_string


@pytest.fixture(autouse=True)
def setup_app(app):
    with resources.as_file(resources.files("tests") / "test_data/test_compute_points_v1") as path:
        app.config["DATA_FOLDER"] = path
    old_lock_datetime = app.config["LOCK_DATETIME"]
    app.config["LOCK_DATETIME"] = str(get_paris_datetime_now() + timedelta(minutes=10))

    with app.app_context():
        initialize_database(app)

    yield app

    app.config["LOCK_DATETIME"] = old_lock_datetime


def test_group_rank(client):
    response_signup = client.post(
        "/api/v1/users/signup",
        json={
            "name": get_random_string(6),
            "first_name": get_random_string(10),
            "last_name": get_random_string(10),
            "password": get_random_string(10),
        },
    )

    assert response_signup.status_code == HTTPStatus.CREATED

    token = response_signup.json["result"]["token"]

    response_all_bets = client.get(
        "/api/v1/bets",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response_all_bets.status_code == HTTPStatus.OK

    new_scores = [(5, 1), (0, 0), (1, 2)]

    for bet, new_score in zip(response_all_bets.json["result"]["score_bets"], new_scores):
        response_patch_bet = client.patch(
            f"/api/v1/score_bets/{bet['id']}",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "team1": {"score": new_score[0]},
                "team2": {"score": new_score[1]},
            },
        )

        assert response_patch_bet.status_code == HTTPStatus.OK

    response_group_result_response = client.get(
        "/api/v1/bets/groups/rank/A",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response_group_result_response.status_code == HTTPStatus.OK
    assert response_group_result_response.json["result"]["group_rank"] == [
        {
            "team": {
                "id": ANY,
                "code": "FR",
                "description": "France",
                "flag": {"url": ANY},
            },
            "drawn": 1,
            "goals_against": 1,
            "goals_difference": 4,
            "goals_for": 5,
            "lost": 0,
            "played": 2,
            "points": 4,
            "won": 1,
        },
        {
            "team": {
                "id": ANY,
                "code": "IM",
                "description": "Isle of Man",
                "flag": {"url": ANY},
            },
            "drawn": 1,
            "goals_against": 1,
            "goals_difference": 1,
            "goals_for": 2,
            "lost": 0,
            "played": 2,
            "points": 4,
            "won": 1,
        },
        {
            "team": {
                "code": "IE",
                "description": "Ireland",
                "id": ANY,
                "flag": {"url": ANY},
            },
            "drawn": 0,
            "goals_against": 7,
            "goals_difference": -5,
            "goals_for": 2,
            "lost": 2,
            "played": 2,
            "points": 0,
            "won": 0,
        },
    ]

    # Error case : retrieve group rank with invalid code
    invalid_group_code = get_random_string(2)

    response_group_rank_with_invalid_code = client.get(
        f"/api/v1/bets/groups/rank/{invalid_group_code}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response_group_rank_with_invalid_code.json == {
        "description": f"Group not found: {invalid_group_code}",
        "error_code": HTTPStatus.NOT_FOUND,
        "ok": False,
    }

    response_patch_bet = client.patch(
        f"/api/v1/score_bets/{response_all_bets.json['result']['score_bets'][0]['id']}",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "team1": {"score": 6},
            "team2": {"score": 5},
        },
    )

    assert response_patch_bet.status_code == HTTPStatus.OK

    response_group_rank_response = client.get(
        "/api/v1/bets/groups/rank/A",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response_group_rank_response.status_code == HTTPStatus.OK
    assert response_group_rank_response.json["result"]["group_rank"] == [
        {
            "team": {
                "id": ANY,
                "code": ANY,
                "description": "France",
                "flag": ANY,
            },
            "played": 2,
            "won": 1,
            "drawn": 1,
            "lost": 0,
            "goals_for": 6,
            "goals_against": 5,
            "goals_difference": 1,
            "points": 4,
        },
        {
            "team": {
                "id": ANY,
                "code": ANY,
                "description": "Isle of Man",
                "flag": ANY,
            },
            "played": 2,
            "won": 1,
            "drawn": 1,
            "lost": 0,
            "goals_for": 2,
            "goals_against": 1,
            "goals_difference": 1,
            "points": 4,
        },
        {
            "team": {
                "id": ANY,
                "code": ANY,
                "description": "Ireland",
                "flag": ANY,
            },
            "played": 2,
            "won": 0,
            "drawn": 0,
            "lost": 2,
            "goals_for": 6,
            "goals_against": 8,
            "goals_difference": -2,
            "points": 0,
        },
    ]

    response_patch_bet = client.patch(
        f"/api/v1/score_bets/{response_all_bets.json['result']['score_bets'][1]['id']}",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "team1": {"score": None},
            "team2": {"score": 5},
        },
    )

    assert response_patch_bet.status_code == HTTPStatus.OK

    response_group_rank_response = client.get(
        "/api/v1/bets/groups/rank/A",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response_group_rank_response.json["result"]["group_rank"] == [
        {
            "team": {
                "id": ANY,
                "code": "FR",
                "description": "France",
                "flag": {"url": ANY},
            },
            "played": 1,
            "won": 1,
            "drawn": 0,
            "lost": 0,
            "goals_for": 6,
            "goals_against": 5,
            "goals_difference": 1,
            "points": 3,
        },
        {
            "team": {
                "id": ANY,
                "code": "IM",
                "description": "Isle of Man",
                "flag": {
                    "url": ANY,
                },
            },
            "played": 1,
            "won": 1,
            "drawn": 0,
            "lost": 0,
            "goals_for": 2,
            "goals_against": 1,
            "goals_difference": 1,
            "points": 3,
        },
        {
            "team": {
                "id": ANY,
                "code": "IE",
                "description": "Ireland",
                "flag": {
                    "url": ANY,
                },
            },
            "played": 2,
            "won": 0,
            "drawn": 0,
            "lost": 2,
            "goals_for": 6,
            "goals_against": 8,
            "goals_difference": -2,
            "points": 0,
        },
    ]

    response_patch_bet = client.patch(
        f"/api/v1/score_bets/{response_all_bets.json['result']['score_bets'][2]['id']}",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "team1": {"score": None},
            "team2": {"score": None},
        },
    )

    assert response_patch_bet.status_code == HTTPStatus.OK

    response_group_rank_response = client.get(
        "/api/v1/bets/groups/rank/A",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response_group_rank_response.json["result"]["group_rank"] == [
        {
            "team": {
                "id": ANY,
                "code": "FR",
                "description": "France",
                "flag": {"url": ANY},
            },
            "played": 1,
            "won": 1,
            "drawn": 0,
            "lost": 0,
            "goals_for": 6,
            "goals_against": 5,
            "goals_difference": 1,
            "points": 3,
        },
        {
            "team": {
                "id": ANY,
                "code": "IM",
                "description": "Isle of Man",
                "flag": {"url": ANY},
            },
            "played": 0,
            "won": 0,
            "drawn": 0,
            "lost": 0,
            "goals_for": 0,
            "goals_against": 0,
            "goals_difference": 0,
            "points": 0,
        },
        {
            "team": {
                "id": ANY,
                "code": "IE",
                "description": "Ireland",
                "flag": {"url": ANY},
            },
            "played": 1,
            "won": 0,
            "drawn": 0,
            "lost": 1,
            "goals_for": 5,
            "goals_against": 6,
            "goals_difference": -1,
            "points": 0,
        },
    ]

    response_patch_bet = client.patch(
        f"/api/v1/score_bets/{response_all_bets.json['result']['score_bets'][0]['id']}",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "team1": {"score": 1},
            "team2": {"score": None},
        },
    )

    assert response_patch_bet.status_code == HTTPStatus.OK

    response_group_rank_response = client.get(
        "/api/v1/bets/groups/rank/A",
        headers={"Authorization": f"Bearer {token}"},
    )

    def sort_group_position(group_position):
        return group_position["team"]["code"]

    assert sorted(
        response_group_rank_response.json["result"]["group_rank"],
        key=sort_group_position,
    ) == sorted(
        [
            {
                "team": {
                    "id": ANY,
                    "code": "IM",
                    "description": "Isle of Man",
                    "flag": {"url": ANY},
                },
                "won": 0,
                "drawn": 0,
                "lost": 0,
                "goals_for": 0,
                "goals_against": 0,
                "goals_difference": 0,
                "played": 0,
                "points": 0,
            },
            {
                "team": {
                    "id": ANY,
                    "code": "FR",
                    "description": "France",
                    "flag": {"url": ANY},
                },
                "won": 0,
                "drawn": 0,
                "lost": 0,
                "goals_for": 0,
                "goals_against": 0,
                "goals_difference": 0,
                "played": 0,
                "points": 0,
            },
            {
                "team": {
                    "id": ANY,
                    "code": "IE",
                    "description": "Ireland",
                    "flag": {"url": ANY},
                },
                "won": 0,
                "drawn": 0,
                "lost": 0,
                "goals_for": 0,
                "goals_against": 0,
                "goals_difference": 0,
                "played": 0,
                "points": 0,
            },
        ],
        key=sort_group_position,
    )

    response_patch_bet = client.patch(
        f"/api/v1/score_bets/{response_all_bets.json['result']['score_bets'][0]['id']}",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "team1": {"score": None},
            "team2": {"score": None},
        },
    )

    assert response_patch_bet.status_code == HTTPStatus.OK

    response_group_rank_response_1 = client.get(
        "/api/v1/bets/groups/rank/A",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response_group_rank_response_1.json == response_group_rank_response.json
