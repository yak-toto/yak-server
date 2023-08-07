from datetime import timedelta
from http import HTTPStatus
from typing import TYPE_CHECKING, List, Optional, Tuple
from unittest.mock import ANY

from starlette.testclient import TestClient

from yak_server.cli.database import initialize_database
from yak_server.helpers.settings import RuleContainer, Rules, get_settings

from .utils import get_random_string
from .utils.mock import create_mock

if TYPE_CHECKING:
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


def patch_score_bets(
    client: TestClient,
    user_name: str,
    new_scores: List[Tuple[Optional[int], Optional[int]]],
):
    # signup admin user
    first_name = get_random_string(6)
    last_name = get_random_string(10)

    response_signup = client.post(
        "/api/v1/users/signup",
        json={
            "name": user_name,
            "first_name": first_name,
            "last_name": last_name,
            "password": get_random_string(12),
        },
    )

    assert response_signup.status_code == HTTPStatus.CREATED

    token = response_signup.json()["result"]["token"]

    response_get_all_bets = client.get("/api/v1/bets", headers={"Authorization": f"Bearer {token}"})

    assert response_get_all_bets.status_code == HTTPStatus.OK

    for bet, new_score in zip(response_get_all_bets.json()["result"]["score_bets"], new_scores):
        response_patch_score_bet = client.patch(
            f"/api/v1/score_bets/{bet['id']}",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "team1": {"score": new_score[0]},
                "team2": {"score": new_score[1]},
            },
        )

        assert response_patch_score_bet.status_code == HTTPStatus.OK

    return first_name, last_name, token


def put_finale_phase(client: TestClient, token: str, is_one_won: Optional[bool]):
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


def test_compute_points(app: "FastAPI", monkeypatch):
    client = TestClient(app)

    app.dependency_overrides[get_settings] = create_mock(
        jwt_expiration_time=10,
        jwt_secret_key=get_random_string(100),
        lock_datetime_shift=timedelta(seconds=10),
        rules=Rules(
            [
                RuleContainer(
                    id="492345de-8d4a-45b6-8b94-d219f2b0c3e9",
                    config={
                        "to_group": "1",
                        "from_phase": "GROUP",
                        "versus": [
                            {
                                "team1": {"rank": 1, "group": "A"},
                                "team2": {"rank": 2, "group": "A"},
                            },
                        ],
                    },
                ),
            ],
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
        create_mock(data_folder="test_compute_points_v1"),
    )
    initialize_database(app)

    # Create 4 accounts and patch bets
    _, _, admin_token = patch_score_bets(client, "admin", [(1, 2), (5, 1), (5, 5)])
    user_first_name, user_last_name, user_token = patch_score_bets(
        client,
        "user",
        [(2, 2), (5, 1), (5, 5)],
    )
    user2_first_name, user2_last_name, user2_token = patch_score_bets(
        client,
        "user2",
        [(2, 0), (2, 0), (1, 4)],
    )
    user3_first_name, user3_last_name, user3_token = patch_score_bets(
        client,
        "user3",
        [(0, 2), (2, 0), (1, 1)],
    )

    # Success case : compute_points call
    response_compute_points = client.post(
        "/api/v1/compute_points",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response_compute_points.status_code == HTTPStatus.OK

    # Error case : check unauthorized admin access to compute_points
    response_compute_points_unauthorized = client.post(
        "/api/v1/compute_points",
        headers={"Authorization": f"Bearer {user_token}"},
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
        headers={"Authorization": f"Bearer {user_token}"},
    )

    assert score_board_response.json()["result"] == [
        {
            "rank": 1,
            "first_name": user3_first_name,
            "full_name": f"{user3_first_name} {user3_last_name}",
            "last_name": user3_last_name,
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
            "first_name": user_first_name,
            "full_name": f"{user_first_name} {user_last_name}",
            "last_name": user_last_name,
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
            "first_name": user2_first_name,
            "full_name": f"{user2_first_name} {user2_last_name}",
            "last_name": user2_last_name,
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
    put_finale_phase(client, admin_token, is_one_won=True)
    put_finale_phase(client, user_token, is_one_won=False)
    put_finale_phase(client, user2_token, is_one_won=True)
    put_finale_phase(client, user3_token, is_one_won=False)

    # Compute points again
    response_compute_points = client.post(
        "/api/v1/compute_points",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response_compute_points.status_code == HTTPStatus.OK

    # Check score board after finale phase bets patch
    score_board_response_after_finale_phase = client.get(
        "/api/v1/score_board",
        headers={"Authorization": f"Bearer {user_token}"},
    )

    assert score_board_response_after_finale_phase.json()["result"] == [
        {
            "rank": 1,
            "first_name": user_first_name,
            "full_name": f"{user_first_name} {user_last_name}",
            "last_name": user_last_name,
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
            "first_name": user3_first_name,
            "full_name": f"{user3_first_name} {user3_last_name}",
            "last_name": user3_last_name,
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
            "first_name": user2_first_name,
            "full_name": f"{user2_first_name} {user2_last_name}",
            "last_name": user2_last_name,
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
        headers={"Authorization": f"Bearer {user_token}"},
    )

    assert response_score_board_v2.json() == {
        "data": {
            "scoreBoardResult": {
                "__typename": "ScoreBoard",
                "users": [
                    {
                        "fullName": f"{user_first_name} {user_last_name}",
                        "result": {
                            "numberMatchGuess": 2,
                            "numberQualifiedTeamsGuess": 2,
                            "numberScoreGuess": 2,
                            "points": 483.0,
                        },
                    },
                    {
                        "fullName": f"{user3_first_name} {user3_last_name}",
                        "result": {
                            "numberMatchGuess": 3,
                            "numberQualifiedTeamsGuess": 2,
                            "numberScoreGuess": 0,
                            "points": 286.0,
                        },
                    },
                    {
                        "fullName": f"{user2_first_name} {user2_last_name}",
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
        headers={"Authorization": f"Bearer {user_token}"},
    )

    assert get_results_response.json()["result"] == {
        "rank": 1,
        "first_name": ANY,
        "last_name": ANY,
        "full_name": ANY,
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
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert get_results_response_admin.json() == {
        "ok": False,
        "error_code": HTTPStatus.UNAUTHORIZED,
        "description": "No results for admin user",
    }