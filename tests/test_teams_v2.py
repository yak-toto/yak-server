from importlib import resources
from operator import itemgetter
from unittest.mock import ANY
from uuid import uuid4

import pytest

from yak_server.cli.database import initialize_database

from .utils import get_random_string


@pytest.fixture(autouse=True)
def setup_app(app):
    with resources.as_file(resources.files("tests") / "test_data/test_teams_v1") as path:
        app.config["DATA_FOLDER"] = path

    with app.app_context():
        initialize_database(app)

    return app


def test_teams(client):
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

    assert response_signup.json["data"]["signupResult"]["__typename"] == "UserWithToken"

    auth_token = response_signup.json["data"]["signupResult"]["token"]

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

    assert response_all_teams.json["data"]["allTeamsResult"]["__typename"] == "AllTeamsSuccessful"
    expected_teams = [
        {
            "id": ANY,
            "code": "GR",
            "description": "Greece",
            "flag": {"url": "https://fake-team-flag_greece.com"},
        },
        {
            "id": ANY,
            "code": "DE",
            "description": "Germany",
            "flag": {"url": "https://fake-team-flag_germany.com"},
        },
        {
            "id": ANY,
            "code": "GD",
            "description": "Grenada",
            "flag": {"url": "https://fake-team-flag_grenada.com"},
        },
        {
            "id": ANY,
            "code": "UA",
            "description": "Ukraine",
            "flag": {"url": "https://fake-team-flag_ukraine.com"},
        },
        {
            "id": ANY,
            "code": "ML",
            "description": "Mali",
            "flag": {"url": "https://fake-team-flag_mali.com"},
        },
        {
            "id": ANY,
            "code": "JM",
            "description": "Jamaica",
            "flag": {"url": "https://fake-team-flag_jamaica.com"},
        },
        {
            "id": ANY,
            "code": "JO",
            "description": "Jordan",
            "flag": {"url": "https://fake-team-flag_jordan.com"},
        },
        {
            "id": ANY,
            "code": "NO",
            "description": "Norway",
            "flag": {"url": "https://fake-team-flag_norway.com"},
        },
    ]

    assert sorted(
        response_all_teams.json["data"]["allTeamsResult"]["teams"],
        key=itemgetter("code"),
    ) == sorted(expected_teams, key=itemgetter("code"))

    team_id = [
        team["id"]
        for team in response_all_teams.json["data"]["allTeamsResult"]["teams"]
        if team["description"] == "Norway"
    ][0]

    response_all_teams_invalid_token = client.post(
        "/api/v2",
        json={
            "query": all_teams_query,
        },
        headers={"Authorization": f"Bearer {auth_token[:12]}{auth_token[15:]}"},
    )

    assert (
        response_all_teams_invalid_token.json["data"]["allTeamsResult"]["__typename"]
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
                "teamId": team_id,
            },
        },
        headers={"Authorization": f"Bearer {auth_token}"},
    )

    assert response_team_by_id.json == {
        "data": {
            "teamByIdResult": {
                "__typename": "Team",
                "code": "NO",
                "description": "Norway",
                "flag": {"url": "https://fake-team-flag_norway.com"},
                "id": team_id,
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

    assert response_team_with_invalid_id.json == {
        "data": {
            "teamByIdResult": {
                "__typename": "TeamByIdNotFound",
                "message": f"Cannot find team with id: {invalid_team_id}",
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

    assert response_team_by_code.json == {
        "data": {
            "teamByCodeResult": {
                "__typename": "Team",
                "code": "NO",
                "description": "Norway",
                "flag": {"url": "https://fake-team-flag_norway.com"},
                "id": team_id,
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

    assert response_team_with_invalid_code.json == {
        "data": {
            "teamByCodeResult": {
                "__typename": "TeamByCodeNotFound",
                "message": "Cannot find team with code: NA",
            },
        },
    }
