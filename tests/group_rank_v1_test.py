from http import HTTPStatus
from typing import TYPE_CHECKING
from unittest.mock import ANY

from starlette.testclient import TestClient

from testing.mock import MockSettings
from testing.util import get_random_string
from yak_server.cli.database import initialize_database

if TYPE_CHECKING:
    import pytest
    from fastapi import FastAPI
    from sqlalchemy import Engine


def test_group_rank(
    app_with_valid_jwt_config: "FastAPI",
    engine_for_test: "Engine",
    monkeypatch: "pytest.MonkeyPatch",
) -> None:
    monkeypatch.setattr(
        "yak_server.cli.database.get_settings",
        MockSettings(data_folder_relative="test_compute_points_v1"),
    )

    initialize_database(engine_for_test, app_with_valid_jwt_config)

    client = TestClient(app_with_valid_jwt_config)

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

    access_token = response_signup.json()["result"]["access_token"]

    response_all_bets = client.get(
        "/api/v1/bets",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert response_all_bets.status_code == HTTPStatus.OK

    new_scores = [(5, 1), (0, 0), (1, 2)]

    for bet, new_score in zip(response_all_bets.json()["result"]["score_bets"], new_scores):
        response_patch_bet = client.patch(
            f"/api/v1/score_bets/{bet['id']}",
            headers={"Authorization": f"Bearer {access_token}"},
            json={
                "team1": {"score": new_score[0]},
                "team2": {"score": new_score[1]},
            },
        )

        assert response_patch_bet.status_code == HTTPStatus.OK

    response_group_result_response = client.get(
        "/api/v1/bets/groups/rank/A",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert response_group_result_response.status_code == HTTPStatus.OK
    assert response_group_result_response.json()["result"]["group_rank"] == [
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
                "description": "Île de Man",
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
                "description": "Irlande",
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
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert response_group_rank_with_invalid_code.json() == {
        "description": f"Group not found: {invalid_group_code}",
        "error_code": HTTPStatus.NOT_FOUND,
        "ok": False,
    }

    response_patch_bet = client.patch(
        f"/api/v1/score_bets/{response_all_bets.json()['result']['score_bets'][0]['id']}",
        headers={"Authorization": f"Bearer {access_token}"},
        json={
            "team1": {"score": 6},
            "team2": {"score": 5},
        },
    )

    assert response_patch_bet.status_code == HTTPStatus.OK

    response_group_rank_response = client.get(
        "/api/v1/bets/groups/rank/A",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert response_group_rank_response.status_code == HTTPStatus.OK
    assert response_group_rank_response.json()["result"]["group_rank"] == [
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
                "description": "Île de Man",
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
                "description": "Irlande",
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
        f"/api/v1/score_bets/{response_all_bets.json()['result']['score_bets'][1]['id']}",
        headers={"Authorization": f"Bearer {access_token}"},
        json={
            "team1": {"score": None},
            "team2": {"score": 5},
        },
    )

    assert response_patch_bet.status_code == HTTPStatus.OK

    response_group_rank_response = client.get(
        "/api/v1/bets/groups/rank/A",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert response_group_rank_response.json()["result"]["group_rank"] == [
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
                "description": "Île de Man",
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
                "description": "Irlande",
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
        f"/api/v1/score_bets/{response_all_bets.json()['result']['score_bets'][2]['id']}",
        headers={"Authorization": f"Bearer {access_token}"},
        json={
            "team1": {"score": None},
            "team2": {"score": None},
        },
    )

    assert response_patch_bet.status_code == HTTPStatus.OK

    response_group_rank_response = client.get(
        "/api/v1/bets/groups/rank/A",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert response_group_rank_response.json()["result"]["group_rank"] == [
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
                "description": "Île de Man",
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
                "description": "Irlande",
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
        f"/api/v1/score_bets/{response_all_bets.json()['result']['score_bets'][0]['id']}",
        headers={"Authorization": f"Bearer {access_token}"},
        json={
            "team1": {"score": 1},
            "team2": {"score": None},
        },
    )

    assert response_patch_bet.status_code == HTTPStatus.OK

    response_group_rank_response = client.get(
        "/api/v1/bets/groups/rank/A",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert sorted(
        response_group_rank_response.json()["result"]["group_rank"],
        key=lambda group_position: group_position["team"]["code"],
    ) == sorted(
        [
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
                    "description": "Irlande",
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
                    "code": "IM",
                    "description": "Île de Man",
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
        # I know that the order is not important but I want to be sure that the test is consistent
        key=lambda group_position: group_position["team"]["code"],  # type: ignore[index]
    )

    response_patch_bet = client.patch(
        f"/api/v1/score_bets/{response_all_bets.json()['result']['score_bets'][0]['id']}",
        headers={"Authorization": f"Bearer {access_token}"},
        json={
            "team1": {"score": None},
            "team2": {"score": None},
        },
    )

    assert response_patch_bet.status_code == HTTPStatus.OK

    response_group_rank_response_1 = client.get(
        "/api/v1/bets/groups/rank/A",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert sorted(
        response_group_rank_response_1.json()["result"]["group_rank"],
        key=lambda group_position: group_position["team"]["code"],
    ) == sorted(
        response_group_rank_response.json()["result"]["group_rank"],
        key=lambda group_position: group_position["team"]["code"],
    )


def test_group_rank_team_not_defined(
    app_with_valid_jwt_config: "FastAPI",
    engine_for_test: "Engine",
    monkeypatch: "pytest.MonkeyPatch",
) -> None:
    monkeypatch.setattr(
        "yak_server.cli.database.get_settings",
        MockSettings(data_folder_relative="test_group_rank_team_not_defined"),
    )

    initialize_database(engine_for_test, app_with_valid_jwt_config)

    client = TestClient(app_with_valid_jwt_config)

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

    access_token = response_signup.json()["result"]["access_token"]

    response_retrieve_bets_group = client.get(
        "/api/v1/bets/groups/A", headers={"Authorization": f"Bearer {access_token}"}
    )

    assert response_retrieve_bets_group.status_code == HTTPStatus.OK

    bet_id = response_retrieve_bets_group.json()["result"]["score_bets"][1]["id"]

    response_modify_score_bet = client.patch(
        f"/api/v1/score_bets/{bet_id}",
        headers={"Authorization": f"Bearer {access_token}"},
        json={"team1": {"score": 2}, "team2": {"score": 0}},
    )

    assert response_modify_score_bet.status_code == HTTPStatus.OK

    response_group_result_response = client.get(
        "/api/v1/bets/groups/rank/A",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert response_group_result_response.status_code == HTTPStatus.OK
