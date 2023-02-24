from http import HTTPStatus
from operator import itemgetter
from unittest.mock import ANY
from uuid import uuid4

import pkg_resources

from yak_server.cli.database import initialize_database


def test_teams(app, client):
    # location of test data
    app.config["DATA_FOLDER"] = pkg_resources.resource_filename(__name__, "test_teams_v1")

    # initialize sql database
    with app.app_context():
        initialize_database(app)

    # Fetch all the teams
    response_get_all_teams = client.get(
        "api/v1/teams",
    )

    assert response_get_all_teams.status_code == HTTPStatus.OK

    excepted_teams = [
        {
            "id": ANY,
            "code": "DE",
            "description": "Germany",
            "flag": {"url": "https://fake-team-flag_germany.com"},
        },
        {"id": ANY, "code": "GR", "description": "Greece", "flag": {"url": ANY}},
        {"id": ANY, "code": "GD", "description": "Grenada", "flag": {"url": ANY}},
        {"id": ANY, "code": "JM", "description": "Jamaica", "flag": {"url": ANY}},
        {"id": ANY, "code": "JO", "description": "Jordan", "flag": {"url": ANY}},
        {
            "id": ANY,
            "code": "ML",
            "description": "Mali",
            "flag": {"url": "https://fake-team-flag_mali.com"},
        },
        {"id": ANY, "code": "NO", "description": "Norway", "flag": {"url": ANY}},
        {"id": ANY, "code": "UA", "description": "Ukraine", "flag": {"url": ANY}},
    ]

    assert sorted(
        response_get_all_teams.json["result"]["teams"],
        key=itemgetter("description"),
    ) == sorted(excepted_teams, key=itemgetter("description"))

    # Fetch one team using code
    response_one_team_by_code = client.get(
        "api/v1/teams/DE",
    )

    assert response_one_team_by_code.json["result"]["team"] == {
        "id": ANY,
        "code": "DE",
        "description": "Germany",
        "flag": {"url": ANY},
    }

    # Fetch one team using id
    team_id = response_one_team_by_code.json["result"]["team"]["id"]

    response_one_team_by_id = client.get(
        f"api/v1/teams/{team_id}",
    )

    assert response_one_team_by_id.json["result"]["team"] == {
        "id": team_id,
        "code": "DE",
        "description": "Germany",
        "flag": {"url": ANY},
    }

    # Try to fetch a team using an invalid team id
    invalid_team_id = f"{team_id}dd"

    response_one_team_with_invalid_id = client.get(
        f"api/v1/teams/{invalid_team_id}",
    )

    assert response_one_team_with_invalid_id.json == {
        "ok": False,
        "error_code": HTTPStatus.BAD_REQUEST,
        "description": f"Invalid team id: {invalid_team_id}. "
        "Retry with a uuid or ISO 3166-1 alpha-2 code",
    }

    # Try to fetch a team using a non existing team id
    non_existing_team_id = str(uuid4())

    response_non_existing_team_id = client.get(
        f"api/v1/teams/{non_existing_team_id}",
    )

    assert response_non_existing_team_id.json == {
        "ok": False,
        "error_code": HTTPStatus.NOT_FOUND,
        "description": f"Team not found: {non_existing_team_id}",
    }
