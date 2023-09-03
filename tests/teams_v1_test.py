from http import HTTPStatus
from operator import itemgetter
from typing import TYPE_CHECKING
from unittest.mock import ANY
from uuid import uuid4

from testing.mock import MockSettings
from yak_server.cli.database import initialize_database

if TYPE_CHECKING:
    import pytest
    from fastapi import FastAPI
    from starlette.testclient import TestClient


def test_teams(app: "FastAPI", client: "TestClient", monkeypatch: "pytest.MonkeyPatch") -> None:
    monkeypatch.setattr(
        "yak_server.cli.database.get_settings",
        MockSettings(data_folder_relative="test_teams_v1"),
    )

    initialize_database(app)

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
        "error_code": HTTPStatus.BAD_REQUEST,
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
        "error_code": HTTPStatus.NOT_FOUND,
        "description": f"Team not found: {non_existing_team_id}",
    }

    # Check flag fetching
    response_retrieve_flag = client.get(
        response_one_team_by_code.json()["result"]["team"]["flag"]["url"],
        follow_redirects=False,
    )

    assert response_retrieve_flag.status_code == HTTPStatus.TEMPORARY_REDIRECT

    # Check flag fetching with invalid team id
    invalid_team_id_with_flag = uuid4()

    response_retrieve_flag_with_invalid_id = client.get(
        f"/api/v1/teams/{invalid_team_id_with_flag}/flag",
    )

    assert response_retrieve_flag_with_invalid_id.status_code == HTTPStatus.NOT_FOUND
    assert response_retrieve_flag_with_invalid_id.json() == {
        "ok": False,
        "error_code": HTTPStatus.NOT_FOUND,
        "description": f"Team not found: {invalid_team_id_with_flag}",
    }
