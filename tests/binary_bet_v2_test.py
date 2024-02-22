from secrets import choice
from typing import TYPE_CHECKING
from uuid import uuid4

import pendulum
from starlette.testclient import TestClient

from testing.mock import MockSettings
from testing.util import get_random_string
from yak_server.cli.database import initialize_database
from yak_server.helpers.settings import get_settings

if TYPE_CHECKING:
    import pytest
    from fastapi import FastAPI


def test_binary_bet(
    app_with_valid_jwt_config: "FastAPI",
    monkeypatch: "pytest.MonkeyPatch",
) -> None:
    client = TestClient(app_with_valid_jwt_config)

    jwt_secret_key = app_with_valid_jwt_config.dependency_overrides[get_settings]().jwt_secret_key

    monkeypatch.setattr(
        "yak_server.cli.database.get_settings",
        MockSettings(data_folder_relative="test_binary_bet"),
    )
    initialize_database(app_with_valid_jwt_config)

    user_name = get_random_string(10)
    password = get_random_string(30)

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
                "firstName": get_random_string(6),
                "lastName": get_random_string(12),
                "password": password,
            },
        },
    )

    assert response_signup.json()["data"]["signupResult"]["__typename"] == "UserWithToken"

    response_login = client.post(
        "/api/v2",
        json={
            "query": """
                mutation Root($userName: String!, $password: String!) {
                    loginResult(userName: $userName, password: $password) {
                        __typename
                        ... on UserWithToken {
                            token
                            binaryBets {
                                id
                            }
                        }
                        ... on InvalidCredentials {
                            message
                        }
                    }
                }
            """,
            "variables": {
                "userName": user_name,
                "password": password,
            },
        },
    )

    assert response_login.json()["data"]["loginResult"]["__typename"] == "UserWithToken"
    token = response_login.json()["data"]["loginResult"]["token"]
    bet_id = response_login.json()["data"]["loginResult"]["binaryBets"][0]["id"]

    mutation_modify_binary_bet = """
        mutation Root($id: UUID!, $isOneWon: Boolean) {
            modifyBinaryBetResult(id: $id, isOneWon: $isOneWon) {
                __typename
                ... on BinaryBet {
                    id
                    group {
                        description
                        phase {
                            description
                        }
                    }
                    team1 {
                        won
                        description
                    }
                    team2 {
                        won
                        description
                    }
                }
                ... on BinaryBetNotFoundForUpdate {
                    message
                }
                ... on LockedBinaryBetError {
                    message
                }
                ... on ExpiredToken {
                    message
                }
                ... on InvalidToken {
                    message
                }
            }
        }
    """

    # Success case : modify binary bet
    is_one_won = choice([True, False, None])

    response_modify_binary_bet = client.post(
        "/api/v2",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "query": mutation_modify_binary_bet,
            "variables": {"id": bet_id, "isOneWon": is_one_won},
        },
    )

    assert response_modify_binary_bet.json() == {
        "data": {
            "modifyBinaryBetResult": {
                "__typename": "BinaryBet",
                "group": {"description": "Groupe A", "phase": {"description": "Phase de groupes"}},
                "id": bet_id,
                "team1": {
                    "description": "France",
                    "won": None if is_one_won is None else is_one_won,
                },
                "team2": {
                    "description": "Allemagne",
                    "won": None if is_one_won is None else not is_one_won,
                },
            },
        },
    }

    # Error case : Modify with invalid id
    invalid_bet_id = str(uuid4())

    response_modify_binary_bet_with_invalid_id = client.post(
        "/api/v2",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "query": mutation_modify_binary_bet,
            "variables": {"id": invalid_bet_id, "isOneWon": True},
        },
    )

    assert response_modify_binary_bet_with_invalid_id.json() == {
        "data": {
            "modifyBinaryBetResult": {
                "__typename": "BinaryBetNotFoundForUpdate",
                "message": "Binary bet not found. Cannot modify a resource that does not exist.",
            },
        },
    }

    # Error case : locked binary bet
    app_with_valid_jwt_config.dependency_overrides[get_settings] = MockSettings(
        jwt_expiration_time=10,
        jwt_secret_key=jwt_secret_key,
        lock_datetime_shift=-pendulum.duration(seconds=10),
    )

    response_modify_locked_binary_bet = client.post(
        "/api/v2",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "query": mutation_modify_binary_bet,
            "variables": {"id": bet_id, "isOneWon": True},
        },
    )

    assert response_modify_locked_binary_bet.json() == {
        "data": {
            "modifyBinaryBetResult": {
                "__typename": "LockedBinaryBetError",
                "message": "Cannot modify binary bet, lock date is exceeded",
            },
        },
    }

    app_with_valid_jwt_config.dependency_overrides[get_settings] = MockSettings(
        jwt_expiration_time=10,
        jwt_secret_key=jwt_secret_key,
        lock_datetime_shift=pendulum.duration(seconds=10),
    )

    # Success case : Retrieve one binary bet
    query_binary_bet = """
        query getBinaryBet($id: UUID!) {
            binaryBetResult(id: $id) {
                __typename
                ... on BinaryBet {
                    id
                    group {
                        description
                        phase {
                            description
                        }
                    }
                    team1 {
                        won
                        description
                    }
                    team2 {
                        won
                        description
                    }
                }
                ... on InvalidToken {
                    message
                }
                ... on ExpiredToken {
                    message
                }
                ... on BinaryBetNotFound {
                    message
                }
            }
        }
    """

    response_retrieve_binary_bet = client.post(
        "/api/v2",
        headers={"Authorization": f"Bearer {token}"},
        json={"query": query_binary_bet, "variables": {"id": bet_id}},
    )

    assert response_retrieve_binary_bet.json() == {
        "data": {
            "binaryBetResult": {
                "__typename": "BinaryBet",
                "group": {"description": "Groupe A", "phase": {"description": "Phase de groupes"}},
                "id": bet_id,
                "team1": {
                    "description": "France",
                    "won": None if is_one_won is None else is_one_won,
                },
                "team2": {
                    "description": "Allemagne",
                    "won": None if is_one_won is None else not is_one_won,
                },
            },
        },
    }

    # Error case : retrieve binary bet with invalid id
    invalid_bet_id = str(uuid4())

    response_binary_with_invalid_id = client.post(
        "/api/v2",
        headers={"Authorization": f"Bearer {token}"},
        json={"query": query_binary_bet, "variables": {"id": invalid_bet_id}},
    )

    assert response_binary_with_invalid_id.json() == {
        "data": {
            "binaryBetResult": {
                "__typename": "BinaryBetNotFound",
                "message": f"Binary bet not found: {invalid_bet_id}",
            },
        },
    }
