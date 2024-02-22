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


def test_group(app_with_valid_jwt_config: "FastAPI", monkeypatch: "pytest.MonkeyPatch") -> None:
    client = TestClient(app_with_valid_jwt_config)

    monkeypatch.setattr(
        "yak_server.cli.database.get_settings",
        MockSettings(data_folder_relative="test_matches_db"),
    )
    initialize_database(app_with_valid_jwt_config)

    # Signup one random user
    user_name = get_random_string(6)
    first_name = get_random_string(10)
    last_name = get_random_string(8)
    password = get_random_string(8)

    response_signup = client.post(
        "/api/v2",
        json={
            "query": """
                mutation Root(
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

    # Success case : Get all groups
    response_all_groups = client.post(
        "/api/v2",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={
            "query": """
                query {
                    allGroupsResult {
                        __typename
                        ... on Groups {
                            groups {
                                id
                                description
                                code
                                phase {
                                    id
                                    code
                                    description
                                }
                            }
                        }
                        ... on InvalidToken {
                            message
                        }
                        ... on ExpiredToken {
                            message
                        }
                    }
                }
            """,
        },
    )

    assert response_all_groups.json()["data"]["allGroupsResult"] == {
        "__typename": "Groups",
        "groups": [
            {
                "id": ANY,
                "description": "Groupe A",
                "code": "A",
                "phase": {
                    "id": ANY,
                    "code": "GROUP",
                    "description": "Phase de groupes",
                },
            },
        ],
    }

    query_group_by_code = """
        query Root($code: ID!) {
            groupByCodeResult(code: $code) {
                __typename
                ... on Group {
                    id
                    description
                    phase {
                        description
                    }
                    scoreBets {
                        id
                        team1 {
                            score
                            description
                        }
                        team2 {
                            score
                            description
                        }
                    }
                }
                ... on InvalidToken {
                    message
                }
                ... on ExpiredToken {
                    message
                }
                ... on GroupByCodeNotFound {
                    message
                }
            }
        }
    """

    # Success case : Get group by code
    response_group_by_code = client.post(
        "/api/v2",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={"query": query_group_by_code, "variables": {"code": "A"}},
    )

    assert response_group_by_code.json()["data"]["groupByCodeResult"] == {
        "__typename": "Group",
        "id": ANY,
        "description": "Groupe A",
        "phase": {"description": "Phase de groupes"},
        "scoreBets": [
            {
                "id": ANY,
                "team1": {"score": None, "description": "Andorre"},
                "team2": {"score": None, "description": "Brésil"},
            },
            {
                "id": ANY,
                "team1": {
                    "score": None,
                    "description": "Burkina Faso",
                },
                "team2": {"score": None, "description": "Guatemala"},
            },
            {
                "id": ANY,
                "team1": {
                    "score": None,
                    "description": "Andorre",
                },
                "team2": {
                    "score": None,
                    "description": "Burkina Faso",
                },
            },
            {
                "id": ANY,
                "team1": {
                    "score": None,
                    "description": "Brésil",
                },
                "team2": {
                    "score": None,
                    "description": "Guatemala",
                },
            },
            {
                "id": ANY,
                "team1": {
                    "score": None,
                    "description": "Andorre",
                },
                "team2": {
                    "score": None,
                    "description": "Guatemala",
                },
            },
            {
                "id": ANY,
                "team1": {
                    "score": None,
                    "description": "Brésil",
                },
                "team2": {
                    "score": None,
                    "description": "Burkina Faso",
                },
            },
        ],
    }

    group_id = response_group_by_code.json()["data"]["groupByCodeResult"]["id"]

    # Error case : check invalid code
    invalid_group_code = "B"

    response_group_with_invalid_code = client.post(
        "/api/v2",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={"query": query_group_by_code, "variables": {"code": invalid_group_code}},
    )

    assert response_group_with_invalid_code.json() == {
        "data": {
            "groupByCodeResult": {
                "__typename": "GroupByCodeNotFound",
                "message": f"Group not found: {invalid_group_code}",
            },
        },
    }

    query_by_id = """
        query Root($id: UUID!) {
            groupByIdResult(id: $id) {
                __typename
                ... on Group {
                    description
                    phase {
                        description
                    }
                }
                ... on InvalidToken {
                    message
                }
                ... on ExpiredToken {
                    message
                }
                ... on GroupByIdNotFound {
                    message
                }
            }
        }
    """

    # Success case : Get group by id
    response_group_by_id = client.post(
        "/api/v2",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={"query": query_by_id, "variables": {"id": group_id}},
    )

    assert response_group_by_id.json() == {
        "data": {
            "groupByIdResult": {
                "__typename": "Group",
                "description": "Groupe A",
                "phase": {"description": "Phase de groupes"},
            },
        },
    }

    # Error case : Get group with invalid id
    invalid_group_id = str(uuid4())

    response_group_with_invalid_id = client.post(
        "/api/v2",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={"query": query_by_id, "variables": {"id": invalid_group_id}},
    )

    assert response_group_with_invalid_id.json() == {
        "data": {
            "groupByIdResult": {
                "__typename": "GroupByIdNotFound",
                "message": f"Group not found: {invalid_group_id}",
            },
        },
    }
