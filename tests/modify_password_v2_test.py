from typing import TYPE_CHECKING
from uuid import uuid4

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
                id
                token
            }
            ... on UserNameAlreadyExists {
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
                firstName
                lastName
                fullName
            }
            ... on InvalidCredentials {
                message
            }
        }
    }
"""

QUERY_MODIFY_USER = """
    mutation Root($id: UUID!, $password: String!) {
        modifyUserResult(id: $id, password: $password) {
            __typename
            ... on UserWithoutSensitiveInfo {
                firstName
                lastName
                fullName
            }
            ... on UserNotFound {
                message
            }
            ... on InvalidToken {
                message
            }
            ... on ExpiredToken {
                message
            }
            ... on UnauthorizedAccessToAdminAPI {
                message
            }
        }
    }
"""


def test_modify_password(app_with_valid_jwt_config: "FastAPI") -> None:
    client = TestClient(app_with_valid_jwt_config)

    # Create admin account
    admin_name = "admin"

    response_signup_admin = client.post(
        "/api/v2",
        json={
            "query": QUERY_SIGNUP,
            "variables": {
                "userName": admin_name,
                "firstName": "admin",
                "lastName": "admin",
                "password": get_random_string(15),
            },
        },
    )

    assert response_signup_admin.json()["data"]["signupResult"]["__typename"] == "UserWithToken"
    authentication_token = response_signup_admin.json()["data"]["signupResult"]["token"]

    # Create non admin user account
    other_user_name = get_random_string(6)
    other_user_first_name = get_random_string(10)
    other_user_last_name = get_random_string(12)
    other_user_password = get_random_string(9)

    response_signup_glepape = client.post(
        "/api/v2",
        json={
            "query": QUERY_SIGNUP,
            "variables": {
                "userName": other_user_name,
                "firstName": other_user_first_name,
                "lastName": other_user_last_name,
                "password": other_user_password,
            },
        },
    )

    assert response_signup_glepape.json()["data"]["signupResult"]["__typename"] == "UserWithToken"
    user_id = response_signup_glepape.json()["data"]["signupResult"]["id"]
    authentication_token_glepape = response_signup_glepape.json()["data"]["signupResult"]["token"]

    # Check update is properly process
    new_password_other_user = get_random_string(15)

    response_modify_password = client.post(
        "/api/v2",
        headers={"Authorization": f"Bearer {authentication_token}"},
        json={
            "query": QUERY_MODIFY_USER,
            "variables": {"id": user_id, "password": new_password_other_user},
        },
    )

    assert (
        response_modify_password.json()["data"]["modifyUserResult"]["__typename"]
        == "UserWithoutSensitiveInfo"
    )
    assert (
        response_modify_password.json()["data"]["modifyUserResult"]["fullName"]
        == f"{other_user_first_name} {other_user_last_name}"
    )

    # Check login successful with the new password
    response_login_glepape = client.post(
        "/api/v2",
        json={
            "query": QUERY_LOGIN,
            "variables": {"userName": other_user_name, "password": new_password_other_user},
        },
    )

    assert response_login_glepape.json()["data"]["loginResult"] == {
        "__typename": "UserWithToken",
        "firstName": other_user_first_name,
        "fullName": f"{other_user_first_name} {other_user_last_name}",
        "lastName": other_user_last_name,
    }

    # Check glepape user cannot update any password
    response_modify_password_with_glepape_user = client.post(
        "/api/v2",
        headers={"Authorization": f"Bearer {authentication_token_glepape}"},
        json={
            "query": QUERY_MODIFY_USER,
            "variables": {"id": user_id, "password": "new_new_password"},
        },
    )

    assert response_modify_password_with_glepape_user.json()["data"]["modifyUserResult"] == {
        "__typename": "UnauthorizedAccessToAdminAPI",
        "message": "Unauthorized access to admin API",
    }

    # Check call is rejected if user_id is invalid
    invalid_user_id = uuid4()

    response_wrong_input = client.post(
        "/api/v2",
        headers={"Authorization": f"Bearer {authentication_token}"},
        json={
            "query": QUERY_MODIFY_USER,
            "variables": {"id": str(invalid_user_id), "password": "new_password_for_unknown_user"},
        },
    )

    assert response_wrong_input.json()["data"]["modifyUserResult"] == {
        "__typename": "UserNotFound",
        "message": f"User not found: {invalid_user_id}",
    }
