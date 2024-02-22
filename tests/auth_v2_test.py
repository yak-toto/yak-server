from typing import TYPE_CHECKING
from unittest.mock import ANY

from starlette.testclient import TestClient

from testing.util import get_random_string

if TYPE_CHECKING:
    from fastapi import FastAPI

QUERY_SIGNUP = """
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
                firstName
                lastName
                fullName
                token
            }
            ... on UserNameAlreadyExists {
                message
            }
            ... on UnsatisfiedPasswordRequirements {
                message
            }
        }
    }
"""

QUERY_LOGIN = """
    mutation Root($userName: String!, $password: String!) {
        loginResult(userName: $userName, password: $password) {
            __typename
            ... on UserWithToken {
                token
            }
            ... on InvalidCredentials {
                message
            }
        }
    }
"""

QUERY_CURRENT_USER = """
    query {
        currentUserResult {
            __typename
            ... on User {
                fullName
            }
            ... on InvalidToken {
                message
            }
            ... on ExpiredToken {
                message
            }
        }
    }
"""


def test_signup_and_login(app_with_valid_jwt_config: "FastAPI") -> None:
    client = TestClient(app_with_valid_jwt_config)

    user_name = get_random_string(10)
    first_name = get_random_string(5)
    last_name = get_random_string(8)
    password = get_random_string(15)

    response_signup = client.post(
        "/api/v2",
        json={
            "query": QUERY_SIGNUP,
            "variables": {
                "userName": user_name,
                "firstName": first_name,
                "lastName": last_name,
                "password": password,
            },
        },
    )

    assert response_signup.json()["data"]["signupResult"]["__typename"] == "UserWithToken"

    response_login = client.post(
        "/api/v2",
        json={
            "query": QUERY_LOGIN,
            "variables": {
                "userName": user_name,
                "password": password,
            },
        },
    )

    assert response_login.json()["data"]["loginResult"]["__typename"] == "UserWithToken"

    auth_token = response_login.json()["data"]["loginResult"]["token"]

    response_current_user = client.post(
        "/api/v2",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={
            "query": QUERY_CURRENT_USER,
        },
    )

    assert response_current_user.json()["data"]["currentUserResult"]["__typename"] == "User"

    response_login_invalid_credentials = client.post(
        "/api/v2",
        json={
            "query": QUERY_LOGIN,
            "variables": {
                "userName": user_name,
                "password": get_random_string(6),
            },
        },
    )

    assert response_login_invalid_credentials.json() == {
        "data": {
            "loginResult": {"__typename": "InvalidCredentials", "message": "Invalid credentials"},
        },
    }


def test_signup_and_invalid_token(app_with_valid_jwt_config: "FastAPI") -> None:
    client = TestClient(app_with_valid_jwt_config)

    user_name = get_random_string(10)
    first_name = get_random_string(5)
    last_name = get_random_string(8)
    password = get_random_string(15)

    response_signup = client.post(
        "/api/v2",
        json={
            "query": QUERY_SIGNUP,
            "variables": {
                "userName": user_name,
                "firstName": first_name,
                "lastName": last_name,
                "password": password,
            },
        },
    )
    assert response_signup.json()["data"]["signupResult"] == {
        "__typename": "UserWithToken",
        "firstName": first_name,
        "lastName": last_name,
        "fullName": f"{first_name} {last_name}",
        "token": ANY,
    }

    authentication_token = response_signup.json()["data"]["signupResult"]["token"]

    query_current_user = {
        "query": """
            query {
                currentUserResult {
                    __typename
                    ... on User {
                        firstName
                        lastName
                        fullName
                        result {
                            numberMatchGuess
                            points
                        }
                        groups {
                            description
                        }
                        phases {
                            description
                        }
                        scoreBets {
                            group {
                                id
                                description
                                phase {
                                    description
                                }
                            }
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
                }
            }
        """,
    }

    response_current_user = client.post(
        "/api/v2",
        headers={"Authorization": f"Bearer {authentication_token}"},
        json=query_current_user,
    )

    assert response_current_user.json()["data"]["currentUserResult"]["__typename"] == "User"
    assert response_current_user.json()["data"]["currentUserResult"]["groups"] == []
    assert response_current_user.json()["data"]["currentUserResult"]["phases"] == []

    # invalidate authentication token and check currentUser query
    # send InvalidToken response
    response_current_user = client.post(
        "/api/v2",
        headers={"Authorization": f"Bearer {authentication_token[:-1]}"},
        json=query_current_user,
    )

    assert response_current_user.json()["data"]["currentUserResult"] == {
        "__typename": "InvalidToken",
        "message": "Invalid token, authentication required",
    }

    response_current_user_invalid_key = client.post(
        "/api/v2",
        headers={"Authorization": f"InvalidKey {authentication_token[:-1]}"},
        json=query_current_user,
    )

    assert response_current_user_invalid_key.json()["data"]["currentUserResult"] == {
        "__typename": "InvalidToken",
        "message": "Invalid token, authentication required",
    }


def test_name_already_exists(app_with_valid_jwt_config: "FastAPI") -> None:
    client = TestClient(app_with_valid_jwt_config)

    user_name = get_random_string(8)

    response_signup = client.post(
        "/api/v2",
        json={
            "query": QUERY_SIGNUP,
            "variables": {
                "userName": user_name,
                "firstName": get_random_string(8),
                "lastName": f"{get_random_string(4)} {get_random_string(5)}",
                "password": get_random_string(10),
            },
        },
    )
    assert response_signup.json()["data"]["signupResult"]["__typename"] == "UserWithToken"

    response_signup_2 = client.post(
        "/api/v2",
        json={
            "query": QUERY_SIGNUP,
            "variables": {
                "userName": user_name,
                "firstName": get_random_string(7),
                "lastName": get_random_string(10),
                "password": get_random_string(5),
            },
        },
    )
    assert response_signup_2.json()["data"]["signupResult"] == {
        "__typename": "UserNameAlreadyExists",
        "message": f"Name already exists: {user_name}",
    }


def test_expired_token(app_with_null_jwt_expiration_time: "FastAPI") -> None:
    client = TestClient(app_with_null_jwt_expiration_time)

    user_name = get_random_string(6)
    password = get_random_string(15)

    response_signup = client.post(
        "/api/v2",
        json={
            "query": QUERY_SIGNUP,
            "variables": {
                "userName": user_name,
                "firstName": get_random_string(2),
                "lastName": get_random_string(8),
                "password": password,
            },
        },
    )

    assert response_signup.json()["data"]["signupResult"]["__typename"] == "UserWithToken"

    auth_token = response_signup.json()["data"]["signupResult"]["token"]

    response_expired_token = client.post(
        "/api/v2",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={
            "query": QUERY_CURRENT_USER,
        },
    )

    assert response_expired_token.json() == {
        "data": {
            "currentUserResult": {
                "__typename": "ExpiredToken",
                "message": "Expired token, re-authentication required",
            },
        },
    }


def test_non_compliant_password(app_with_valid_jwt_config: "FastAPI") -> None:
    client = TestClient(app_with_valid_jwt_config)

    response_signup = client.post(
        "/api/v2",
        json={
            "query": QUERY_SIGNUP,
            "variables": {
                "userName": get_random_string(3),
                "firstName": get_random_string(2),
                "lastName": get_random_string(8),
                "password": get_random_string(6),
            },
        },
    )

    assert response_signup.json() == {
        "data": {
            "signupResult": {
                "__typename": "UnsatisfiedPasswordRequirements",
                "message": "Password is too short. Minimum size is 8.",
            }
        }
    }
