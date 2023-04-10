import sys

if sys.version_info >= (3, 9):
    from importlib import resources
else:
    import importlib_resources as resources

from unittest.mock import ANY
from uuid import uuid4

import pytest

from yak_server.cli.database import initialize_database

from .utils import get_random_string


@pytest.fixture(autouse=True)
def setup_app(app):
    # location of test data
    with resources.as_file(resources.files("tests") / "test_data/test_matches_db") as path:
        app.config["DATA_FOLDER"] = path

    # initialize sql database
    with app.app_context():
        initialize_database(app)

    return app


def test_group(client):
    # Signup one random user
    user_name = get_random_string(6)
    first_name = get_random_string(10)
    last_name = get_random_string(8)
    password = get_random_string(5)

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

    assert response_signup.json["data"]["signupResult"]["__typename"] == "UserWithToken"

    auth_token = response_signup.json["data"]["signupResult"]["token"]

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

    assert response_all_groups.json["data"]["allGroupsResult"] == {
        "__typename": "Groups",
        "groups": [
            {
                "id": ANY,
                "description": "Groupe A",
                "code": "A",
                "phase": {
                    "id": ANY,
                    "code": "GROUP",
                    "description": "Group stage",
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

    assert response_group_by_code.json["data"]["groupByCodeResult"] == {
        "__typename": "Group",
        "id": ANY,
        "description": "Groupe A",
        "phase": {"description": "Group stage"},
        "scoreBets": [
            {
                "id": ANY,
                "team1": {"score": None, "description": "Andorra"},
                "team2": {"score": None, "description": "Brazil"},
            },
            {
                "id": ANY,
                "team1": {
                    "score": None,
                    "description": "Burkina Faso",
                },
                "team2": {"score": None, "description": "The Republic of Guatemala"},
            },
            {
                "id": ANY,
                "team1": {
                    "score": None,
                    "description": "Andorra",
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
                    "description": "Brazil",
                },
                "team2": {
                    "score": None,
                    "description": "The Republic of Guatemala",
                },
            },
            {
                "id": ANY,
                "team1": {
                    "score": None,
                    "description": "Andorra",
                },
                "team2": {
                    "score": None,
                    "description": "The Republic of Guatemala",
                },
            },
            {
                "id": ANY,
                "team1": {
                    "score": None,
                    "description": "Brazil",
                },
                "team2": {
                    "score": None,
                    "description": "Burkina Faso",
                },
            },
        ],
    }

    group_id = response_group_by_code.json["data"]["groupByCodeResult"]["id"]

    # Error case : check invalid code
    invalid_group_code = "B"

    response_group_with_invalid_code = client.post(
        "/api/v2",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={"query": query_group_by_code, "variables": {"code": invalid_group_code}},
    )

    assert response_group_with_invalid_code.json == {
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

    assert response_group_by_id.json == {
        "data": {
            "groupByIdResult": {
                "__typename": "Group",
                "description": "Groupe A",
                "phase": {"description": "Group stage"},
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

    assert response_group_with_invalid_id.json == {
        "data": {
            "groupByIdResult": {
                "__typename": "GroupByIdNotFound",
                "message": f"Group not found: {invalid_group_id}",
            },
        },
    }
