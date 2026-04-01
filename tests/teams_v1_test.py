from http import HTTPStatus
from operator import itemgetter
from typing import TYPE_CHECKING
from unittest.mock import ANY
from uuid import uuid4

from starlette.testclient import TestClient

from testing.mock import MockSettings
from testing.util import get_resources_path
from yak_server.cli.database import initialize_database
from yak_server.helpers.settings import get_settings

if TYPE_CHECKING:
    from fastapi import FastAPI
    from sqlalchemy import Engine


def test_teams(app_with_valid_jwt_config: "FastAPI", engine_for_test: "Engine") -> None:
    initialize_database(engine_for_test, get_resources_path("test_teams_v1"))

    app_with_valid_jwt_config.dependency_overrides[get_settings] = MockSettings(
        data_folder_relative="test_teams_v1",
        competition="test_teams_v1",
    )

    client = TestClient(app_with_valid_jwt_config)

    # Fetch all the teams
    response_get_all_teams = client.get("api/v1/teams")

    assert response_get_all_teams.status_code == HTTPStatus.OK

    excepted_teams = [
        {
            "id": ANY,
            "code": "DE",
            "description": "Allemagne",
            "flag": {"url": ANY},
        },
        {"id": ANY, "code": "GR", "description": "Grèce", "flag": {"url": ANY}},
        {"id": ANY, "code": "GD", "description": "Grenade", "flag": {"url": ANY}},
        {"id": ANY, "code": "JM", "description": "Jamaïque", "flag": {"url": ANY}},
        {"id": ANY, "code": "JO", "description": "Jordanie", "flag": {"url": ANY}},
        {
            "id": ANY,
            "code": "ML",
            "description": "Mali",
            "flag": {"url": ANY},
        },
        {"id": ANY, "code": "NO", "description": "Norvège", "flag": {"url": ANY}},
        {"id": ANY, "code": "UA", "description": "Ukraine", "flag": {"url": ANY}},
    ]

    assert sorted(
        response_get_all_teams.json()["result"]["teams"],
        key=itemgetter("description"),
    ) == sorted(excepted_teams, key=itemgetter("description"))

    # Fetch one team using code
    response_one_team_by_code = client.get(
        "api/v1/teams/DE",
    )

    assert response_one_team_by_code.json()["result"]["team"] == {
        "id": ANY,
        "code": "DE",
        "description": "Allemagne",
        "flag": {"url": ANY},
    }

    # Fetch one team using id
    team_id = response_one_team_by_code.json()["result"]["team"]["id"]

    response_one_team_by_id = client.get(
        f"api/v1/teams/{team_id}",
    )

    assert response_one_team_by_id.json()["result"]["team"] == {
        "id": team_id,
        "code": "DE",
        "description": "Allemagne",
        "flag": {"url": ANY},
    }

    # Try to fetch a team using an invalid team id
    invalid_team_id = f"{team_id}dd"

    response_one_team_with_invalid_id = client.get(
        f"api/v1/teams/{invalid_team_id}",
    )

    assert response_one_team_with_invalid_id.json() == {
        "ok": False,
        "error_code": "invalid_team_id",
        "description": (
            f"Invalid team id: {invalid_team_id}. Retry with a uuid or ISO 3166-1 alpha-2 code"
        ),
    }

    # Try to fetch a team using a non existing team id
    non_existing_team_id = uuid4()

    response_non_existing_team_id = client.get(
        f"api/v1/teams/{non_existing_team_id}",
    )

    assert response_non_existing_team_id.json() == {
        "ok": False,
        "error_code": "team_not_found",
        "description": f"Team not found: {non_existing_team_id}",
    }

    # Check flag fetching
    response_retrieve_flag = client.get(
        f"/api/v1/teams/{response_one_team_by_code.json()['result']['team']['id']}/flag",
        follow_redirects=False,
    )

    assert response_retrieve_flag.status_code == HTTPStatus.OK

    # Check flag fetching for a team whose flag file is missing on disk
    # GR has a fake flag path blanked to "" by initialize_database
    gr_id = client.get("api/v1/teams/GR").json()["result"]["team"]["id"]

    response_retrieve_missing_flag = client.get(f"/api/v1/teams/{gr_id}/flag")

    assert response_retrieve_missing_flag.status_code == HTTPStatus.NOT_FOUND
    assert response_retrieve_missing_flag.json() == {
        "ok": False,
        "error_code": "team_flag_not_found",
        "description": f"Team flag not found: {gr_id}",
    }

    # Check flag fetching with invalid team id
    invalid_team_id_with_flag = uuid4()

    response_retrieve_flag_with_invalid_id = client.get(
        f"/api/v1/teams/{invalid_team_id_with_flag}/flag",
    )

    assert response_retrieve_flag_with_invalid_id.status_code == HTTPStatus.NOT_FOUND
    assert response_retrieve_flag_with_invalid_id.json() == {
        "ok": False,
        "error_code": "team_not_found",
        "description": f"Team not found: {invalid_team_id_with_flag}",
    }
