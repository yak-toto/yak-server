from datetime import datetime, timedelta
from http import HTTPStatus
from importlib import resources
from unittest.mock import ANY

from yak_server.cli.database import initialize_database

from .test_utils import get_random_string


def patch_score_bets(client, user_name, new_scores):
    # signup admin user
    response_signup = client.post(
        "/api/v1/users/signup",
        json={
            "name": user_name,
            "first_name": get_random_string(6),
            "last_name": get_random_string(10),
            "password": get_random_string(12),
        },
    )

    assert response_signup.status_code == HTTPStatus.CREATED

    token = response_signup.json["result"]["token"]

    response_get_all_bets = client.get("/api/v1/bets", headers={"Authorization": f"Bearer {token}"})

    assert response_get_all_bets.status_code == HTTPStatus.OK

    for bet, new_score in zip(response_get_all_bets.json["result"]["score_bets"], new_scores):
        response_patch_score_bet = client.patch(
            f"/api/v1/score_bets/{bet['id']}",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "team1": {"score": new_score[0]},
                "team2": {"score": new_score[1]},
            },
        )

        assert response_patch_score_bet.status_code == HTTPStatus.OK

    return token


def put_finale_phase(client, token, is_one_won):
    response_post_finale_phase_bets_admin = client.post(
        "/api/v1/bets/finale_phase",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response_post_finale_phase_bets_admin.status_code == HTTPStatus.OK

    response_put_finale_phase = client.put(
        "/api/v1/bets/phases/FINAL",
        json=[
            {
                "is_one_won": is_one_won,
                "index": 1,
                "group": {
                    "id": response_post_finale_phase_bets_admin.json["result"]["groups"][0]["id"],
                },
                "team1": {
                    "id": response_post_finale_phase_bets_admin.json["result"]["binary_bets"][0][
                        "team1"
                    ]["id"],
                },
                "team2": {
                    "id": response_post_finale_phase_bets_admin.json["result"]["binary_bets"][0][
                        "team2"
                    ]["id"],
                },
            },
        ],
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response_put_finale_phase.status_code == HTTPStatus.OK


def test_compute_points(app, client):
    # location of test data
    with resources.as_file(resources.files("tests") / "test_compute_points_v1") as path:
        app.config["DATA_FOLDER"] = path
    app.config["LOCK_DATETIME"] = str(datetime.now() + timedelta(minutes=10))
    app.config["LOCK_DATETIME_FINAL_PHASE"] = str(datetime.now() + timedelta(minutes=10))
    app.config["FINALE_PHASE_CONFIG"] = {
        "first_group": "1",
        "versus": [{"team1": {"rank": 1, "group": "A"}, "team2": {"rank": 2, "group": "A"}}],
    }

    with app.app_context():
        initialize_database(app)

    # Create 4 accounts and patch bets
    admin_token = patch_score_bets(client, "admin", [(1, 2), (5, 1), (5, 5)])
    user_token = patch_score_bets(client, "user", [(2, 2), (5, 1), (5, 5)])
    user2_token = patch_score_bets(client, "user2", [(2, 0), (2, 0), (1, 4)])
    user3_token = patch_score_bets(client, "user3", [(0, 2), (2, 0), (1, 1)])

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
    assert response_compute_points_unauthorized.json == {
        "ok": False,
        "error_code": HTTPStatus.UNAUTHORIZED,
        "description": "Unauthorized access to admin API",
    }

    # Success case : Check score board call
    score_board_response = client.get(
        "/api/v1/score_board",
        headers={"Authorization": f"Bearer {user_token}"},
    )

    assert score_board_response.json["result"] == [
        {
            "first_name": ANY,
            "full_name": ANY,
            "last_name": ANY,
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
            "first_name": ANY,
            "full_name": ANY,
            "last_name": ANY,
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
            "first_name": ANY,
            "full_name": ANY,
            "last_name": ANY,
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
    put_finale_phase(client, admin_token, True)
    put_finale_phase(client, user_token, False)
    put_finale_phase(client, user2_token, True)
    put_finale_phase(client, user3_token, False)

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

    assert score_board_response_after_finale_phase.json["result"] == [
        {
            "first_name": ANY,
            "full_name": ANY,
            "last_name": ANY,
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
            "first_name": ANY,
            "full_name": ANY,
            "last_name": ANY,
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
            "first_name": ANY,
            "full_name": ANY,
            "last_name": ANY,
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
        headers={"Authorization": f"Bearer {user_token}"},
    )

    assert get_results_response.json["result"] == {
        "first_name": ANY,
        "full_name": ANY,
        "last_name": ANY,
        "number_final_guess": 2,
        "number_first_qualified_guess": 0,
        "number_match_guess": 2,
        "number_qualified_teams_guess": 2,
        "number_quarter_final_guess": 0,
        "number_score_guess": 2,
        "number_semi_final_guess": 0,
        "number_winner_guess": 1,
        "points": 483.0,
        "rank": 1,
    }

    # Error case : check not result for admin user
    get_results_response_admin = client.get(
        "/api/v1/results",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert get_results_response_admin.json == {
        "ok": False,
        "error_code": HTTPStatus.UNAUTHORIZED,
        "description": "No results for admin user",
    }
