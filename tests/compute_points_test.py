from http import HTTPStatus
from typing import TYPE_CHECKING, Optional

import pendulum
from starlette.testclient import TestClient
from typer.testing import CliRunner

from testing.mock import MockSettings
from testing.util import UserData, get_random_string, patch_score_bets
from yak_server.cli import app as cli_app
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

QUERY_SCORE_BOARD = """
    query {
        scoreBoardResult {
            __typename
            ... on ScoreBoard {
                users {
                    fullName
                    result {
                        numberMatchGuess
                        numberScoreGuess
                        numberQualifiedTeamsGuess
                        points
                    }
                }
            }
            ... on InvalidToken {
                message
            }
            ... on ExpiredToken {
                message
            }
        }
    }
"""


def put_finale_phase(client: TestClient, token: str, *, is_one_won: Optional[bool]) -> None:
    response_post_finale_phase_bets_admin = client.post(
        "/api/v1/rules/492345de-8d4a-45b6-8b94-d219f2b0c3e9",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response_post_finale_phase_bets_admin.json() == {"ok": True, "result": ""}
    assert response_post_finale_phase_bets_admin.status_code == HTTPStatus.OK

    response_get_finale_phase = client.get(
        "/api/v1/bets/phases/FINAL",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response_get_finale_phase.status_code == HTTPStatus.OK

    response_patch_finale_phase = client.patch(
        f"/api/v1/binary_bets/{response_get_finale_phase.json()['result']['binary_bets'][0]['id']}",
        json={"is_one_won": is_one_won},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response_patch_finale_phase.status_code == HTTPStatus.OK


def test_compute_points(app: "FastAPI", monkeypatch: "pytest.MonkeyPatch") -> None:
    client = TestClient(app)

    rules = Rules(
        compute_finale_phase_from_group_rank=RuleComputeFinaleFromGroupRank(
            to_group="1",
            from_phase="GROUP",
            versus=[Versus(team1=Team(rank=1, group="A"), team2=Team(rank=2, group="A"))],
        ),
        compute_points=RuleComputePoints(
            base_correct_result=1,
            multiplying_factor_correct_result=2,
            base_correct_score=3,
            multiplying_factor_correct_score=7,
            team_qualified=10,
            first_team_qualified=20,
        ),
    )

    app.dependency_overrides[get_settings] = MockSettings(
        jwt_expiration_time=10,
        jwt_secret_key=get_random_string(100),
        lock_datetime_shift=pendulum.duration(seconds=10),
        rules=rules,
        base_correct_result=1,
        multiplying_factor_correct_result=2,
        base_correct_score=3,
        multiplying_factor_correct_score=7,
        team_qualified=10,
        first_team_qualified=20,
    )

    monkeypatch.setattr(
        "yak_server.cli.database.get_settings",
        MockSettings(data_folder_relative="test_compute_points_v1"),
    )
    initialize_database(app)

    # Signup admin
    admin = UserData(
        first_name=get_random_string(10),
        last_name=get_random_string(12),
        name="admin",
        scores=[(1, 2), (5, 1), (5, 5)],
    )

    response_signup_admin = client.post(
        "/api/v1/users/signup",
        json={
            "first_name": admin.first_name,
            "last_name": admin.last_name,
            "name": admin.name,
            "password": get_random_string(85),
        },
    )

    assert response_signup_admin.status_code == HTTPStatus.CREATED

    admin.token = response_signup_admin.json()["result"]["token"]

    # Patch admin scores
    patch_score_bets(client, admin.token, admin.scores)

    # Signup 3 players and patch their scores
    users_data = [
        UserData(
            first_name=get_random_string(15),
            last_name=get_random_string(15),
            name="user1",
            scores=[(2, 2), (5, 1), (5, 5)],
        ),
        UserData(
            first_name=get_random_string(15),
            last_name=get_random_string(15),
            name="user2",
            scores=[(2, 0), (2, 0), (1, 4)],
        ),
        UserData(
            first_name=get_random_string(15),
            last_name=get_random_string(15),
            name="user3",
            scores=[(0, 2), (2, 0), (1, 1)],
        ),
    ]

    for user_data in users_data:
        response_signup = client.post(
            "/api/v1/users/signup",
            json={
                "name": user_data.name,
                "first_name": user_data.first_name,
                "last_name": user_data.last_name,
                "password": get_random_string(18),
            },
        )

        assert response_signup.status_code == HTTPStatus.CREATED

        user_data.token = response_signup.json()["result"]["token"]

        patch_score_bets(client, user_data.token, user_data.scores)

    # Success case : compute_points call
    response_compute_points = client.post(
        "/api/v1/rules/62d46542-8cf1-4a3b-af77-a5086f10ac59",
        headers={"Authorization": f"Bearer {admin.token}"},
    )

    assert response_compute_points.status_code == HTTPStatus.OK

    # Error case : check unauthorized admin access to compute_points
    response_compute_points_unauthorized = client.post(
        "/api/v1/rules/62d46542-8cf1-4a3b-af77-a5086f10ac59",
        headers={"Authorization": f"Bearer {users_data[0].token}"},
    )

    assert response_compute_points_unauthorized.status_code == HTTPStatus.UNAUTHORIZED
    assert response_compute_points_unauthorized.json() == {
        "ok": False,
        "error_code": HTTPStatus.UNAUTHORIZED,
        "description": "Unauthorized access to admin API",
    }

    # Success case : Check score board call
    score_board_response = client.get(
        "/api/v1/score_board",
        headers={"Authorization": f"Bearer {users_data[0].token}"},
    )

    assert score_board_response.json()["result"] == [
        {
            "rank": 1,
            "first_name": users_data[2].first_name,
            "full_name": f"{users_data[2].first_name} {users_data[2].last_name}",
            "last_name": users_data[2].last_name,
            "number_final_guess": 0,
            "number_first_qualified_guess": 1,
            "number_match_guess": 3,
            "number_qualified_teams_guess": 2,
            "number_quarter_final_guess": 0,
            "number_score_guess": 0,
            "number_semi_final_guess": 0,
            "number_winner_guess": 0,
            "points": 46.0,
        },
        {
            "rank": 2,
            "first_name": users_data[0].first_name,
            "full_name": f"{users_data[0].first_name} {users_data[0].last_name}",
            "last_name": users_data[0].last_name,
            "number_final_guess": 0,
            "number_first_qualified_guess": 0,
            "number_match_guess": 2,
            "number_qualified_teams_guess": 2,
            "number_quarter_final_guess": 0,
            "number_score_guess": 2,
            "number_semi_final_guess": 0,
            "number_winner_guess": 0,
            "points": 43.0,
        },
        {
            "rank": 3,
            "first_name": users_data[1].first_name,
            "full_name": f"{users_data[1].first_name} {users_data[1].last_name}",
            "last_name": users_data[1].last_name,
            "number_final_guess": 0,
            "number_first_qualified_guess": 0,
            "number_match_guess": 1,
            "number_qualified_teams_guess": 1,
            "number_quarter_final_guess": 0,
            "number_score_guess": 0,
            "number_semi_final_guess": 0,
            "number_winner_guess": 0,
            "points": 11.0,
        },
    ]

    # Push finale phase bets
    put_finale_phase(client, admin.token, is_one_won=True)
    put_finale_phase(client, users_data[0].token, is_one_won=False)
    put_finale_phase(client, users_data[1].token, is_one_won=True)
    put_finale_phase(client, users_data[2].token, is_one_won=False)

    # Compute points again with cli

    monkeypatch.setattr("yak_server.cli.database.get_settings", MockSettings(rules=rules))

    runner = CliRunner()

    result = runner.invoke(cli_app, ["db", "score-board"])

    assert result.exit_code == 0

    # Check score board after finale phase bets patch
    score_board_response_after_finale_phase = client.get(
        "/api/v1/score_board",
        headers={"Authorization": f"Bearer {users_data[0].token}"},
    )

    assert score_board_response_after_finale_phase.json()["result"] == [
        {
            "rank": 1,
            "first_name": users_data[0].first_name,
            "full_name": f"{users_data[0].first_name} {users_data[0].last_name}",
            "last_name": users_data[0].last_name,
            "number_final_guess": 2,
            "number_first_qualified_guess": 0,
            "number_match_guess": 2,
            "number_qualified_teams_guess": 2,
            "number_quarter_final_guess": 0,
            "number_score_guess": 2,
            "number_semi_final_guess": 0,
            "number_winner_guess": 1,
            "points": 483.0,
        },
        {
            "rank": 2,
            "first_name": users_data[2].first_name,
            "full_name": f"{users_data[2].first_name} {users_data[2].last_name}",
            "last_name": users_data[2].last_name,
            "number_final_guess": 2,
            "number_first_qualified_guess": 1,
            "number_match_guess": 3,
            "number_qualified_teams_guess": 2,
            "number_quarter_final_guess": 0,
            "number_score_guess": 0,
            "number_semi_final_guess": 0,
            "number_winner_guess": 0,
            "points": 286.0,
        },
        {
            "rank": 3,
            "first_name": users_data[1].first_name,
            "full_name": f"{users_data[1].first_name} {users_data[1].last_name}",
            "last_name": users_data[1].last_name,
            "number_final_guess": 1,
            "number_first_qualified_guess": 0,
            "number_match_guess": 1,
            "number_qualified_teams_guess": 1,
            "number_quarter_final_guess": 0,
            "number_score_guess": 0,
            "number_semi_final_guess": 0,
            "number_winner_guess": 0,
            "points": 131.0,
        },
    ]

    # Check score board
    response_score_board_v2 = client.post(
        "/api/v2",
        json={"query": QUERY_SCORE_BOARD},
        headers={"Authorization": f"Bearer {users_data[0].token}"},
    )

    assert response_score_board_v2.json() == {
        "data": {
            "scoreBoardResult": {
                "__typename": "ScoreBoard",
                "users": [
                    {
                        "fullName": f"{users_data[0].first_name} {users_data[0].last_name}",
                        "result": {
                            "numberMatchGuess": 2,
                            "numberQualifiedTeamsGuess": 2,
                            "numberScoreGuess": 2,
                            "points": 483.0,
                        },
                    },
                    {
                        "fullName": f"{users_data[2].first_name} {users_data[2].last_name}",
                        "result": {
                            "numberMatchGuess": 3,
                            "numberQualifiedTeamsGuess": 2,
                            "numberScoreGuess": 0,
                            "points": 286.0,
                        },
                    },
                    {
                        "fullName": f"{users_data[1].first_name} {users_data[1].last_name}",
                        "result": {
                            "numberMatchGuess": 1,
                            "numberQualifiedTeamsGuess": 1,
                            "numberScoreGuess": 0,
                            "points": 131.0,
                        },
                    },
                ],
            },
        },
    }

    # Success case : check user GET /results call
    get_results_response = client.get(
        "/api/v1/results",
        headers={"Authorization": f"Bearer {users_data[0].token}"},
    )

    assert get_results_response.json()["result"] == {
        "rank": 1,
        "first_name": users_data[0].first_name,
        "last_name": users_data[0].last_name,
        "full_name": f"{users_data[0].first_name} {users_data[0].last_name}",
        "number_final_guess": 2,
        "number_first_qualified_guess": 0,
        "number_match_guess": 2,
        "number_qualified_teams_guess": 2,
        "number_quarter_final_guess": 0,
        "number_score_guess": 2,
        "number_semi_final_guess": 0,
        "number_winner_guess": 1,
        "points": 483.0,
    }

    # Error case : check not result for admin user
    get_results_response_admin = client.get(
        "/api/v1/results",
        headers={"Authorization": f"Bearer {admin.token}"},
    )

    assert get_results_response_admin.json() == {
        "ok": False,
        "error_code": HTTPStatus.UNAUTHORIZED,
        "description": "No results for admin user",
    }
