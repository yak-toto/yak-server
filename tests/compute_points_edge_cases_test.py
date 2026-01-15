from collections.abc import Generator
from http import HTTPStatus
from typing import TYPE_CHECKING
from unittest.mock import ANY

import pytest
from fastapi import status
from starlette.testclient import TestClient

from testing.mock import MockSettings
from testing.util import UserData, get_random_string, get_resources_path, patch_score_bets
from yak_server.cli.admin import create_admin
from yak_server.cli.database import initialize_database
from yak_server.database.models import Role, UserModel
from yak_server.database.session import build_local_session_maker
from yak_server.helpers.rules import Rules
from yak_server.helpers.rules.compute_final_from_rank import (
    RuleComputeFinaleFromGroupRank,
    Team,
    Versus,
    compute_finale_phase_from_group_rank,
)
from yak_server.helpers.rules.compute_points import RuleComputePoints
from yak_server.helpers.settings import get_settings

if TYPE_CHECKING:
    from fastapi import FastAPI
    from sqlalchemy import Engine


@pytest.fixture
def app_with_rules_and_score_board_config(
    app_with_valid_jwt_config: "FastAPI",
) -> Generator["FastAPI", None, None]:
    app_with_valid_jwt_config.dependency_overrides[get_settings] = MockSettings(
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
    )

    yield app_with_valid_jwt_config

    app_with_valid_jwt_config.dependency_overrides.clear()


def test_compute_points(
    app_with_rules_and_score_board_config: "FastAPI", engine_for_test: "Engine"
) -> None:
    client = TestClient(app_with_rules_and_score_board_config)

    initialize_database(
        engine_for_test,
        app_with_rules_and_score_board_config,
        get_resources_path("test_compute_points_edge_cases_v1"),
    )

    admin = UserData(
        name="admin",
        first_name=get_random_string(15),
        last_name=get_random_string(10),
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

    password = get_random_string(15)

    create_admin(password, engine_for_test)

    response_login_admin = client.post(
        "/api/v1/users/login",
        json={"name": admin.name, "password": password},
    )

    assert response_login_admin.status_code == HTTPStatus.CREATED

    admin.access_token = response_login_admin.json()["result"]["access_token"]

    # Patch score bet admin
    patch_score_bets(client, admin.access_token, admin.scores)

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

        user.access_token = response_signup.json()["result"]["access_token"]

        patch_score_bets(client, user.access_token, user.scores)

    # Success case : compute_points call
    response_compute_points = client.post(
        "/api/v1/rules/62d46542-8cf1-4a3b-af77-a5086f10ac59",
        headers={"Authorization": f"Bearer {admin.access_token}"},
    )

    assert response_compute_points.status_code == HTTPStatus.OK

    # Check final rule execution
    rule_final_phase_response = client.post(
        "/api/v1/rules/492345de-8d4a-45b6-8b94-d219f2b0c3e9",
        headers={"Authorization": f"Bearer {users_data[0].access_token}"},
    )

    assert rule_final_phase_response.status_code == HTTPStatus.OK

    # Check retrieve all bets after final phase
    bets_final_phase_response = client.get(
        "/api/v1/bets/phases/FINAL",
        headers={"Authorization": f"Bearer {users_data[0].access_token}"},
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
        headers={"Authorization": f"Bearer {users_data[0].access_token}"},
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
        admin.access_token,
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
        headers={"Authorization": f"Bearer {admin.access_token}"},
    )

    # Check again score board
    score_board_response = client.get(
        "/api/v1/score_board",
        headers={"Authorization": f"Bearer {users_data[0].access_token}"},
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


def test_missing_first_phase_group(engine_for_test: "Engine") -> None:
    to_group = "2"

    rule = RuleComputeFinaleFromGroupRank(
        to_group=to_group,
        from_phase="GROUP",
        versus=[
            Versus(team1=Team(rank=1, group="A"), team2=Team(rank=2, group="B")),
            Versus(team1=Team(rank=1, group="B"), team2=Team(rank=2, group="A")),
        ],
    )

    local_session_maker = build_local_session_maker(engine_for_test)

    user = UserModel(
        name="fake_user",
        first_name="fake",
        last_name="user",
        password=get_random_string(150),
        role=Role.USER,
    )

    with local_session_maker() as db:
        assert compute_finale_phase_from_group_rank(db, user, rule) == (
            status.HTTP_404_NOT_FOUND,
            "Group not found with code: 2",
        )


def test_no_bet_associated_to_first_phase_group(
    app_with_valid_jwt_config: "FastAPI", engine_for_test: "Engine"
) -> None:
    initialize_database(
        engine_for_test,
        app_with_valid_jwt_config,
        get_resources_path("test_no_bet_associated_to_first_phase_group"),
    )

    client = TestClient(app_with_valid_jwt_config)

    response = client.post(
        "/api/v1/users/signup",
        json={
            "name": "fake_user",
            "first_name": "fake",
            "last_name": "user",
            "password": get_random_string(15),
        },
    )

    assert response.status_code == HTTPStatus.CREATED

    user_id = response.json()["result"]["id"]
    access_token = response.json()["result"]["access_token"]

    response_get_all_bets = client.get(
        "/api/v1/bets",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response_get_all_bets.status_code == HTTPStatus.OK
    bet_id = response_get_all_bets.json()["result"]["score_bets"][0]["id"]

    response = client.patch(
        f"/api/v1/score_bets/{bet_id}",
        headers={"Authorization": f"Bearer {access_token}"},
        json={"team1": {"score": 4}, "team2": {"score": 2}},
    )

    assert response.status_code == HTTPStatus.OK

    local_session_maker = build_local_session_maker(engine_for_test)

    rule = RuleComputeFinaleFromGroupRank(
        to_group="1",
        from_phase="GROUP",
        versus=[Versus(team1=Team(rank=1, group="A"), team2=Team(rank=2, group="A"))],
    )

    with local_session_maker() as db:
        user = db.query(UserModel).filter_by(id=user_id).first()

        assert user is not None
        assert compute_finale_phase_from_group_rank(db, user, rule) == (status.HTTP_200_OK, "")
