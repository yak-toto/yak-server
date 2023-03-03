from datetime import datetime, timedelta
from http import HTTPStatus
from unittest.mock import ANY

import pkg_resources

from yak_server.cli.database import initialize_database

from .test_utils import get_random_string


def test_group_result(app, client):
    app.config["DATA_FOLDER"] = pkg_resources.resource_filename(__name__, "test_compute_points_v1")
    app.config["LOCK_DATETIME"] = str(datetime.now() + timedelta(minutes=10))

    with app.app_context():
        initialize_database(app)

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

    response_patch_bets = client.patch(
        "/api/v1/bets",
        json=[
            {
                "id": bet["id"],
                "team1": {"score": new_scores[index][0]},
                "team2": {"score": new_scores[index][1]},
            }
            for index, bet in enumerate(response_all_bets.json["result"]["score_bets"])
        ],
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response_patch_bets.status_code == HTTPStatus.OK

    response_group_result_response = client.get(
        "/api/v1/bets/groups/results/A",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response_group_result_response.status_code == HTTPStatus.OK
    assert response_group_result_response.json["result"]["results"] == [
        {
            "code": "FR",
            "description": "France",
            "drawn": 1,
            "flag": {"url": "https://fake-team-flag_france.com"},
            "goals_against": 1,
            "goals_difference": 4,
            "goals_for": 5,
            "id": ANY,
            "lost": 0,
            "played": 2,
            "points": 4,
            "won": 1,
        },
        {
            "code": "IM",
            "description": "Isle of Man",
            "drawn": 1,
            "flag": {"url": "https://fake-team-flag_isle_of_man.com"},
            "goals_against": 1,
            "goals_difference": 1,
            "goals_for": 2,
            "id": ANY,
            "lost": 0,
            "played": 2,
            "points": 4,
            "won": 1,
        },
        {
            "code": "IE",
            "description": "Ireland",
            "drawn": 0,
            "flag": {"url": "https://fake-team-flag_brazil.com"},
            "goals_against": 7,
            "goals_difference": -5,
            "goals_for": 2,
            "id": ANY,
            "lost": 2,
            "played": 2,
            "points": 0,
            "won": 0,
        },
    ]
