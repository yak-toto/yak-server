import sys
from http import HTTPStatus

if sys.version_info >= (3, 9):
    from importlib import resources
else:
    import importlib_resources as resources

from unittest.mock import ANY

import pytest

from yak_server.cli.database import initialize_database

from .utils import get_random_string


@pytest.fixture(autouse=True)
def setup_app(app):
    with resources.as_file(resources.files("tests") / "test_data/test_compute_points_v1") as path:
        app.config["DATA_FOLDER"] = path

    with app.app_context():
        initialize_database(app)

    return app


def test_bets_by_groups(client):
    response_signup = client.post(
        "/api/v1/users/signup",
        json={
            "name": get_random_string(6),
            "first_name": get_random_string(6),
            "last_name": get_random_string(6),
            "password": get_random_string(6),
        },
    )

    assert response_signup.status_code == HTTPStatus.CREATED

    token = response_signup.json["result"]["token"]

    # Success case
    bets_by_valid_group = client.get(
        "/api/v1/bets/groups/A",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert bets_by_valid_group.json["result"] == {
        "binary_bets": [],
        "group": {
            "code": "A",
            "description": "Groupe A",
            "id": ANY,
        },
        "phase": {
            "code": "GROUP",
            "description": "Group stage",
            "id": ANY,
        },
        "score_bets": [
            {
                "id": ANY,
                "index": 1,
                "locked": True,
                "team1": {
                    "code": "FR",
                    "description": "France",
                    "flag": {"url": ANY},
                    "id": ANY,
                    "score": None,
                },
                "team2": {
                    "code": "IE",
                    "description": "Ireland",
                    "flag": {"url": ANY},
                    "id": ANY,
                    "score": None,
                },
            },
            {
                "id": ANY,
                "index": 2,
                "locked": True,
                "team1": {
                    "code": "FR",
                    "description": "France",
                    "flag": {"url": ANY},
                    "id": ANY,
                    "score": None,
                },
                "team2": {
                    "code": "IM",
                    "description": "Isle of Man",
                    "flag": {"url": ANY},
                    "id": ANY,
                    "score": None,
                },
            },
            {
                "id": ANY,
                "index": 3,
                "locked": True,
                "team1": {
                    "code": "IE",
                    "description": "Ireland",
                    "flag": {"url": ANY},
                    "id": ANY,
                    "score": None,
                },
                "team2": {
                    "code": "IM",
                    "description": "Isle of Man",
                    "flag": {"url": ANY},
                    "id": ANY,
                    "score": None,
                },
            },
        ],
    }

    # Error case : invalid group code
    invalid_group_code = "B"

    bets_by_invalid_group_code = client.get(
        f"/api/v1/bets/groups/{invalid_group_code}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert bets_by_invalid_group_code.json == {
        "ok": False,
        "error_code": HTTPStatus.NOT_FOUND,
        "description": f"Group not found: {invalid_group_code}",
    }
