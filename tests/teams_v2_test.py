from operator import itemgetter
from typing import TYPE_CHECKING
from unittest.mock import ANY
from uuid import uuid4

from starlette.testclient import TestClient

from testing.mock import MockSettings
from testing.util import get_random_string
from yak_server.cli.database import initialize_database

if TYPE_CHECKING:
    import pytest
    from fastapi import FastAPI


def test_teams(app_with_valid_jwt_config: "FastAPI", monkeypatch: "pytest.MonkeyPatch") -> None:
    client = TestClient(app_with_valid_jwt_config)

    monkeypatch.setattr(
        "yak_server.cli.database.get_settings",
        MockSettings(data_folder_relative="test_teams_v1"),
    )
    initialize_database(app_with_valid_jwt_config)

    user_name = get_random_string(6)
    first_name = get_random_string(10)
    last_name = get_random_string(2)
    password = get_random_string(20)

    response_signup = client.post(
        "/api/v2",
        json={
            "query": """
                mutation Signup(
                    $userName: String!, $firstName: String!,
                    $lastName: String!, $password: String!
                ) {
                    signupResult(
                        userName: $userName, firstName: $firstName,
                        lastName: $lastName, password: $password
                    ) {
                        __typename
                        ... on UserWithToken {
                            token
                        }
                        ... on UserNameAlreadyExists {
                            message
                        }
                    }
                }
            """,
            "variables": {
                "userName": user_name,
                "firstName": first_name,
                "lastName": last_name,
                "password": password,
            },
        },
    )

    assert response_signup.json()["data"]["signupResult"]["__typename"] == "UserWithToken"

    auth_token = response_signup.json()["data"]["signupResult"]["token"]

    all_teams_query = """
        query {
            allTeamsResult {
                __typename
                ... on AllTeamsSuccessful {
                    teams {
                        id
                        code
                        description
                        flag {
                            url
                        }
                    }
                }
                ... on InvalidToken {
                    __typename
                    message
                }
                ... on ExpiredToken {
                    __typename
                    message
                }
            }
        }
    """

    response_all_teams = client.post(
        "/api/v2",
        json={
            "query": all_teams_query,
        },
        headers={"Authorization": f"Bearer {auth_token}"},
    )

    assert response_all_teams.json()["data"]["allTeamsResult"]["__typename"] == "AllTeamsSuccessful"
    expected_teams = [
        {
            "id": ANY,
            "code": "GR",
            "description": "Grèce",
            "flag": {"url": ANY},
        },
        {
            "id": ANY,
            "code": "DE",
            "description": "Allemagne",
            "flag": {"url": ANY},
        },
        {
            "id": ANY,
            "code": "GD",
            "description": "Grenade",
            "flag": {"url": ANY},
        },
        {
            "id": ANY,
            "code": "UA",
            "description": "Ukraine",
            "flag": {"url": ANY},
        },
        {
            "id": ANY,
            "code": "ML",
            "description": "Mali",
            "flag": {"url": ANY},
        },
        {
            "id": ANY,
            "code": "JM",
            "description": "Jamaïque",
            "flag": {"url": ANY},
        },
        {
            "id": ANY,
            "code": "JO",
            "description": "Jordanie",
            "flag": {"url": ANY},
        },
        {
            "id": ANY,
            "code": "NO",
            "description": "Norvège",
            "flag": {"url": ANY},
        },
    ]

    for team in expected_teams:
        assert f"/api/v1/teams/{team['id']}/flag" == team["flag"]["url"]

    assert sorted(
        response_all_teams.json()["data"]["allTeamsResult"]["teams"],
        key=itemgetter("code"),
    ) == sorted(expected_teams, key=itemgetter("code"))

    team_norway = [
        team
        for team in response_all_teams.json()["data"]["allTeamsResult"]["teams"]
        if team["description"] == "Norvège"
    ]

    assert len(team_norway) == 1

    team_norway_id = team_norway[0]["id"]

    response_all_teams_invalid_token = client.post(
        "/api/v2",
        json={
            "query": all_teams_query,
        },
        headers={"Authorization": f"Bearer {auth_token[:12]}{auth_token[15:]}"},
    )

    assert (
        response_all_teams_invalid_token.json()["data"]["allTeamsResult"]["__typename"]
        == "InvalidToken"
    )

    team_by_id_query = """
        query Root($teamId: UUID!) {
            teamByIdResult(id: $teamId) {
                __typename
                ... on Team {
                    id
                    code
                    description
                    flag {
                        url
                    }
                }
                ... on InvalidToken {
                    message
                }
                ... on ExpiredToken {
                    message
                }
                ... on TeamByIdNotFound {
                    message
                }
            }
        }
    """

    response_team_by_id = client.post(
        "/api/v2",
        json={
            "query": team_by_id_query,
            "variables": {
                "teamId": team_norway_id,
            },
        },
        headers={"Authorization": f"Bearer {auth_token}"},
    )

    assert response_team_by_id.json() == {
        "data": {
            "teamByIdResult": {
                "__typename": "Team",
                "code": "NO",
                "description": "Norvège",
                "flag": {"url": f"/api/v1/teams/{team_norway_id}/flag"},
                "id": team_norway_id,
            },
        },
    }

    invalid_team_id = str(uuid4())

    response_team_with_invalid_id = client.post(
        "/api/v2",
        json={
            "query": team_by_id_query,
            "variables": {
                "teamId": invalid_team_id,
            },
        },
        headers={"Authorization": f"Bearer {auth_token}"},
    )

    assert response_team_with_invalid_id.json() == {
        "data": {
            "teamByIdResult": {
                "__typename": "TeamByIdNotFound",
                "message": f"Team not found: {invalid_team_id}",
            },
        },
    }

    team_by_code_query = """
        query Root($teamCode: String!) {
            teamByCodeResult(code: $teamCode) {
                __typename
                ... on Team {
                    id
                    code
                    description
                    flag {
                        url
                    }
                }
                ... on InvalidToken {
                    message
                }
                ... on ExpiredToken {
                    message
                }
                ... on TeamByCodeNotFound {
                    message
                }
            }
        }
    """

    response_team_by_code = client.post(
        "/api/v2",
        json={
            "query": team_by_code_query,
            "variables": {
                "teamCode": "NO",
            },
        },
        headers={"Authorization": f"Bearer {auth_token}"},
    )

    assert response_team_by_code.json() == {
        "data": {
            "teamByCodeResult": {
                "__typename": "Team",
                "code": "NO",
                "description": "Norvège",
                "flag": {"url": f"/api/v1/teams/{team_norway_id}/flag"},
                "id": team_norway_id,
            },
        },
    }

    response_team_with_invalid_code = client.post(
        "/api/v2",
        json={
            "query": team_by_code_query,
            "variables": {
                "teamCode": "NA",
            },
        },
        headers={"Authorization": f"Bearer {auth_token}"},
    )

    assert response_team_with_invalid_code.json() == {
        "data": {
            "teamByCodeResult": {
                "__typename": "TeamByCodeNotFound",
                "message": "Team not found: NA",
            },
        },
    }
