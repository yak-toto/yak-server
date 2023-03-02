from datetime import datetime, timedelta
from http import HTTPStatus
from unittest.mock import ANY

import pkg_resources

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

    response_patch_score_bet = client.patch(
        "/api/v1/bets",
        json=[
            {
                "id": bet["id"],
                "team1": {"score": new_scores[index][0]},
                "team2": {"score": new_scores[index][1]},
            }
            for index, bet in enumerate(response_get_all_bets.json["result"]["score_bets"])
        ],
        headers={"Authorization": f"Bearer {token}"},
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

    if response_put_finale_phase.status_code == HTTPStatus.UNAUTHORIZED:
        assert response_put_finale_phase.json["description"] == ""


def test_compute_points(app, client):
    # location of test data
    app.config["DATA_FOLDER"] = pkg_resources.resource_filename(__name__, "test_compute_points_v1")
    app.config["LOCK_DATETIME"] = str(datetime.now() + timedelta(minutes=10))
    app.config["LOCK_DATETIME_FINAL_PHASE"] = str(datetime.now() + timedelta(minutes=10))
    app.config["FINALE_PHASE_CONFIG"] = {
        "first_group": "1",
        "versus": [{"team1": {"rank": 1, "group": "A"}, "team2": {"rank": 2, "group": "A"}}],
    }

    with app.app_context():
        initialize_database(app)

    admin_token = patch_score_bets(client, "admin", [(1, 2), (5, 1), (5, 5)])

    user_token = patch_score_bets(client, "user", [(2, 2), (5, 1), (5, 5)])

    user2_token = patch_score_bets(client, "user2", [(2, 0), (2, 0), (1, 4)])

    user3_token = patch_score_bets(client, "user3", [(0, 2), (2, 0), (1, 1)])

    response_compute_points = client.post(
        "/api/v1/compute_points",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response_compute_points.status_code == HTTPStatus.OK

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

    put_finale_phase(client, admin_token, True)
    put_finale_phase(client, user_token, False)
    put_finale_phase(client, user2_token, True)
    put_finale_phase(client, user3_token, False)

    response_compute_points = client.post(
        "/api/v1/compute_points",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response_compute_points.status_code == HTTPStatus.OK

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
