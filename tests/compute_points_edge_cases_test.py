from http import HTTPStatus
from typing import TYPE_CHECKING
from unittest.mock import ANY

import pendulum
from starlette.testclient import TestClient

from testing.mock import MockSettings
from testing.util import UserData, get_random_string, patch_score_bets
from yak_server.cli.database import initialize_database
from yak_server.helpers.rules import Rules
from yak_server.helpers.rules.compute_final_from_rank import (
    RuleComputeFinaleFromGroupRank,
    Team,
    Versus,
)
from yak_server.helpers.rules.compute_points import RuleComputePoints
from yak_server.helpers.settings import get_settings

if TYPE_CHECKING:
    import pytest
    from fastapi import FastAPI


def test_compute_points(app: "FastAPI", monkeypatch: "pytest.MonkeyPatch") -> None:
    client = TestClient(app)

    app.dependency_overrides[get_settings] = MockSettings(
        jwt_expiration_time=10,
        jwt_secret_key=get_random_string(100),
        lock_datetime_shift=pendulum.duration(minutes=10),
        rules=Rules(
            compute_finale_phase_from_group_rank=RuleComputeFinaleFromGroupRank(
                to_group="2",
                from_phase="GROUP",
                versus=[
                    Versus(team1=Team(rank=1, group="A"), team2=Team(rank=2, group="B")),
                    Versus(team1=Team(rank=1, group="B"), team2=Team(rank=2, group="A")),
                ],
            ),
            compute_points=RuleComputePoints(
                base_correct_result=1,
                multiplying_factor_correct_result=2,
                base_correct_score=3,
                multiplying_factor_correct_score=7,
                team_qualified=10,
                first_team_qualified=20,
            ),
        ),
        base_correct_result=1,
        multiplying_factor_correct_result=2,
        base_correct_score=3,
        multiplying_factor_correct_score=7,
        team_qualified=10,
        first_team_qualified=20,
    )

    monkeypatch.setattr(
        "yak_server.cli.database.get_settings",
        MockSettings(data_folder_relative="test_compute_points_edge_cases_v1"),
    )
    initialize_database(app)

    admin = UserData(
        name="admin",
        first_name="admin",
        last_name="admin",
        scores=[
            (1, 2),
            (5, 1),
            (5, 5),
            (2, 2),
            (3, 0),
            (2, 5),
            (5, 3),
            (1, 1),
            (6, 5),
            (1, 1),
            (1, 1),
            (2, 0),
        ],
    )

    response_signup_admin = client.post(
        "/api/v1/users/signup",
        json={
            "name": admin.name,
            "first_name": admin.first_name,
            "last_name": admin.last_name,
            "password": get_random_string(15),
        },
    )

    assert response_signup_admin.status_code == HTTPStatus.CREATED

    admin.token = response_signup_admin.json()["result"]["token"]

    # Patch score bet admin
    patch_score_bets(client, admin.token, admin.scores)

    # Signup 3 players and patch their scores
    users_data = [
        UserData(
            name=get_random_string(6),
            first_name=get_random_string(15),
            last_name=get_random_string(16),
            scores=[
                (4, 1),
                (2, 6),
                (1, 2),
                (4, 3),
                (1, 1),
                (0, 0),
                (2, 2),
                (3, 0),
                (6, 0),
                (None, 2),
                (None, 3),
                (5, 0),
            ],
        ),
        UserData(
            name=get_random_string(7),
            first_name=get_random_string(89),
            last_name=get_random_string(25),
            scores=[
                (4, 5),
                (3, 0),
                (None, 3),
                (0, 3),
                (0, None),
                (5, 4),
                (2, None),
                (1, 5),
                (0, 3),
                (None, None),
                (2, None),
                (2, None),
            ],
        ),
        UserData(
            name=get_random_string(26),
            first_name=get_random_string(14),
            last_name=get_random_string(85),
            scores=[
                (2, 6),
                (0, None),
                (0, None),
                (3, 2),
                (2, None),
                (0, 3),
                (6, 3),
                (0, 5),
                (3, 4),
                (2, None),
                (6, 4),
                (3, None),
            ],
        ),
    ]

    for user in users_data:
        response_signup = client.post(
            "/api/v1/users/signup",
            json={
                "first_name": user.first_name,
                "last_name": user.last_name,
                "name": user.name,
                "password": get_random_string(85),
            },
        )

        assert response_signup.status_code == HTTPStatus.CREATED

        user.token = response_signup.json()["result"]["token"]

        patch_score_bets(client, user.token, user.scores)

    # Success case : compute_points call
    response_compute_points = client.post(
        "/api/v1/rules/62d46542-8cf1-4a3b-af77-a5086f10ac59",
        headers={"Authorization": f"Bearer {admin.token}"},
    )

    assert response_compute_points.status_code == HTTPStatus.OK

    # Check final rule execution
    rule_final_phase_response = client.post(
        "/api/v1/rules/492345de-8d4a-45b6-8b94-d219f2b0c3e9",
        headers={"Authorization": f"Bearer {users_data[0].token}"},
    )

    assert rule_final_phase_response.status_code == HTTPStatus.OK

    # Check retrieve all bets after final phase
    bets_final_phase_response = client.get(
        "/api/v1/bets/phases/FINAL", headers={"Authorization": f"Bearer {users_data[0].token}"}
    )

    assert bets_final_phase_response.status_code == HTTPStatus.OK

    semi_finals_id = bets_final_phase_response.json()["result"]["groups"][0]["id"]
    finale_id = bets_final_phase_response.json()["result"]["groups"][1]["id"]

    assert bets_final_phase_response.json() == {
        "ok": True,
        "result": {
            "phase": {"id": ANY, "code": "FINAL", "description": "Phase finale"},
            "groups": [
                {"id": semi_finals_id, "code": "2", "description": "Demi-finale"},
                {"id": finale_id, "code": "1", "description": "Final"},
            ],
            "score_bets": [],
            "binary_bets": [
                {
                    "id": ANY,
                    "locked": False,
                    "group": {"id": semi_finals_id},
                    "team1": None,
                    "team2": None,
                },
                {
                    "id": ANY,
                    "locked": False,
                    "group": {"id": semi_finals_id},
                    "team1": None,
                    "team2": None,
                },
                {
                    "id": ANY,
                    "locked": False,
                    "group": {"id": finale_id},
                    "team1": None,
                    "team2": None,
                },
            ],
        },
    }

    # Success case : Check score board call
    score_board_response = client.get(
        "/api/v1/score_board",
        headers={"Authorization": f"Bearer {users_data[0].token}"},
    )

    assert score_board_response.json()["result"] == [
        {
            "rank": 1,
            "first_name": users_data[0].first_name,
            "last_name": users_data[0].last_name,
            "full_name": f"{users_data[0].first_name} {users_data[0].last_name}",
            "number_match_guess": 2,
            "number_score_guess": 0,
            "number_qualified_teams_guess": 1,
            "number_first_qualified_guess": 0,
            "number_quarter_final_guess": 0,
            "number_semi_final_guess": 0,
            "number_final_guess": 0,
            "number_winner_guess": 0,
            "points": 16.0,
        },
        {
            "rank": 2,
            "first_name": users_data[2].first_name,
            "last_name": users_data[2].last_name,
            "full_name": f"{users_data[2].first_name} {users_data[2].last_name}",
            "number_match_guess": 3,
            "number_score_guess": 0,
            "number_qualified_teams_guess": 0,
            "number_first_qualified_guess": 0,
            "number_quarter_final_guess": 0,
            "number_semi_final_guess": 0,
            "number_final_guess": 0,
            "number_winner_guess": 0,
            "points": 8.0,
        },
        {
            "rank": 3,
            "first_name": users_data[1].first_name,
            "last_name": users_data[1].last_name,
            "full_name": f"{users_data[1].first_name} {users_data[1].last_name}",
            "number_match_guess": 2,
            "number_score_guess": 0,
            "number_qualified_teams_guess": 0,
            "number_first_qualified_guess": 0,
            "number_quarter_final_guess": 0,
            "number_semi_final_guess": 0,
            "number_final_guess": 0,
            "number_winner_guess": 0,
            "points": 5.0,
        },
    ]

    # Patch admin score bets so all groups are not filled
    patch_score_bets(
        client,
        admin.token,
        [
            (1, 0),
            None,
            (1, 0),
            None,
            (None, 0),
            (5, 2),
            (None, None),
            (1, 0),
            (2, 0),
            (None, 5),
            (2, None),
            (None, None),
        ],
    )

    # Compute points again
    response_compute_points = client.post(
        "/api/v1/rules/62d46542-8cf1-4a3b-af77-a5086f10ac59",
        headers={"Authorization": f"Bearer {admin.token}"},
    )

    # Check again score board
    score_board_response = client.get(
        "/api/v1/score_board",
        headers={"Authorization": f"Bearer {users_data[0].token}"},
    )

    assert score_board_response.json()["result"] == [
        {
            "rank": 1,
            "first_name": users_data[0].first_name,
            "last_name": users_data[0].last_name,
            "full_name": f"{users_data[0].first_name} {users_data[0].last_name}",
            "number_match_guess": 3,
            "number_score_guess": 0,
            "number_qualified_teams_guess": 1,
            "number_first_qualified_guess": 0,
            "number_quarter_final_guess": 0,
            "number_semi_final_guess": 0,
            "number_final_guess": 0,
            "number_winner_guess": 0,
            "points": 9.0,
        },
        {
            "rank": 2,
            "first_name": users_data[1].first_name,
            "last_name": users_data[1].last_name,
            "full_name": f"{users_data[1].first_name} {users_data[1].last_name}",
            "number_match_guess": 2,
            "number_score_guess": 0,
            "number_qualified_teams_guess": 0,
            "number_first_qualified_guess": 0,
            "number_quarter_final_guess": 0,
            "number_semi_final_guess": 0,
            "number_final_guess": 0,
            "number_winner_guess": 0,
            "points": 6.0,
        },
        {
            "rank": 3,
            "first_name": users_data[2].first_name,
            "last_name": users_data[2].last_name,
            "full_name": f"{users_data[2].first_name} {users_data[2].last_name}",
            "number_match_guess": 0,
            "number_score_guess": 0,
            "number_qualified_teams_guess": 0,
            "number_first_qualified_guess": 0,
            "number_quarter_final_guess": 0,
            "number_semi_final_guess": 0,
            "number_final_guess": 0,
            "number_winner_guess": 0,
            "points": 0.0,
        },
    ]
