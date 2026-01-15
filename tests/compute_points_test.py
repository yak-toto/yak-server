from collections.abc import Generator
from http import HTTPStatus
from typing import TYPE_CHECKING

import pytest
from click.testing import CliRunner
from starlette.testclient import TestClient

from testing.mock import MockSettings
from testing.util import UserData, get_random_string, get_resources_path, patch_score_bets
from yak_server.cli import app as cli_app
from yak_server.cli.admin import create_admin
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
    from fastapi import FastAPI
    from sqlalchemy import Engine


def put_finale_phase(client: TestClient, access_token: str, *, is_one_won: bool | None) -> None:
    response_post_finale_phase_bets_admin = client.post(
        "/api/v1/rules/492345de-8d4a-45b6-8b94-d219f2b0c3e9",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert response_post_finale_phase_bets_admin.json() == {"ok": True, "result": ""}
    assert response_post_finale_phase_bets_admin.status_code == HTTPStatus.OK

    response_get_finale_phase = client.get(
        "/api/v1/bets/phases/FINAL",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert response_get_finale_phase.status_code == HTTPStatus.OK

    response_patch_finale_phase = client.patch(
        f"/api/v1/binary_bets/{response_get_finale_phase.json()['result']['binary_bets'][0]['id']}",
        json={"is_one_won": is_one_won},
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert response_patch_finale_phase.status_code == HTTPStatus.OK


@pytest.fixture
def app_and_rules_for_compute_points(
    app_with_valid_jwt_config: "FastAPI",
) -> Generator[tuple["FastAPI", Rules], None, None]:
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

    app_with_valid_jwt_config.dependency_overrides[get_settings] = MockSettings(rules=rules)

    yield app_with_valid_jwt_config, rules

    app_with_valid_jwt_config.dependency_overrides.clear()


def test_compute_points(
    app_and_rules_for_compute_points: tuple["FastAPI", Rules],
    engine_for_test: "Engine",
    monkeypatch: "pytest.MonkeyPatch",
) -> None:
    app, rules = app_and_rules_for_compute_points

    client = TestClient(app)

    initialize_database(engine_for_test, app, get_resources_path("test_compute_points_v1"))

    # Signup admin
    password = get_random_string(15)

    admin = UserData(
        first_name=get_random_string(10),
        last_name=get_random_string(12),
        name="admin",
        scores=[(1, 2), (5, 1), (5, 5)],
    )

    create_admin(password, engine_for_test)

    response_login_admin = client.post(
        "/api/v1/users/login",
        json={
            "name": admin.name,
            "password": password,
        },
    )

    assert response_login_admin.status_code == HTTPStatus.CREATED

    admin.access_token = response_login_admin.json()["result"]["access_token"]

    # Patch admin scores
    patch_score_bets(client, admin.access_token, admin.scores)

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

        user_data.access_token = response_signup.json()["result"]["access_token"]

        patch_score_bets(client, user_data.access_token, user_data.scores)

    # Success case : compute_points call
    response_compute_points = client.post(
        "/api/v1/rules/62d46542-8cf1-4a3b-af77-a5086f10ac59",
        headers={"Authorization": f"Bearer {admin.access_token}"},
    )

    assert response_compute_points.status_code == HTTPStatus.OK

    # Error case : check unauthorized admin access to compute_points
    response_compute_points_unauthorized = client.post(
        "/api/v1/rules/62d46542-8cf1-4a3b-af77-a5086f10ac59",
        headers={"Authorization": f"Bearer {users_data[0].access_token}"},
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
        headers={"Authorization": f"Bearer {users_data[0].access_token}"},
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
    put_finale_phase(client, admin.access_token, is_one_won=True)
    put_finale_phase(client, users_data[0].access_token, is_one_won=False)
    put_finale_phase(client, users_data[1].access_token, is_one_won=True)
    put_finale_phase(client, users_data[2].access_token, is_one_won=False)

    # Compute points again with cli
    monkeypatch.setattr("yak_server.cli.score_board.get_settings", MockSettings(rules=rules))

    runner = CliRunner()

    result = runner.invoke(cli_app, ["db", "score-board"])

    assert result.exit_code == 0

    # Check score board after finale phase bets patch
    score_board_response_after_finale_phase = client.get(
        "/api/v1/score_board",
        headers={"Authorization": f"Bearer {users_data[0].access_token}"},
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

    # Success case : check user GET /results call
    get_results_response = client.get(
        "/api/v1/results",
        headers={"Authorization": f"Bearer {users_data[0].access_token}"},
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
        headers={"Authorization": f"Bearer {admin.access_token}"},
    )

    assert get_results_response_admin.json() == {
        "ok": False,
        "error_code": HTTPStatus.UNAUTHORIZED,
        "description": "No results for admin user",
    }
