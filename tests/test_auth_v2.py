from unittest.mock import ANY

from .test_utils import get_random_string


def test_signup_and_login(client):
    user_name = get_random_string(10)
    first_name = get_random_string(5)
    last_name = get_random_string(8)
    password = get_random_string(15)

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

    response_login = client.post(
        "/api/v2",
        json={
            "query": """
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
            """,
            "variables": {
                "userName": user_name,
                "password": password,
            },
        },
    )

    assert response_login.json["data"]["loginResult"]["__typename"] == "UserWithToken"

    auth_token = response_login.json["data"]["loginResult"]["token"]

    response_current_user = client.post(
        "/api/v2",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={
            "query": """
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
            """,
        },
    )

    assert response_current_user.json["data"]["currentUserResult"]["__typename"] == "User"

    response_login_invalid_credentials = client.post(
        "/api/v2",
        json={
            "query": """
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
            """,
            "variables": {
                "userName": user_name,
                "password": get_random_string(6),
            },
        },
    )

    assert response_login_invalid_credentials.json == {
        "data": {
            "loginResult": {"__typename": "InvalidCredentials", "message": "Invalid credentials"},
        },
    }


def test_signup_and_invalid_token(client):
    user_name = get_random_string(10)
    first_name = get_random_string(5)
    last_name = get_random_string(8)
    password = get_random_string(15)

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
                            firstName
                            lastName
                            fullName
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
    assert response_signup.json["data"]["signupResult"] == {
        "__typename": "UserWithToken",
        "firstName": first_name,
        "lastName": last_name,
        "fullName": f"{first_name} {last_name}",
        "token": ANY,
    }

    authentification_token = response_signup.json["data"]["signupResult"]["token"]

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
        headers={"Authorization": f"Bearer {authentification_token}"},
        json=query_current_user,
    )

    assert response_current_user.json["data"]["currentUserResult"]["__typename"] == "User"

    # invalidate authentification token and check currentUser query
    # send InvalidToken response
    response_current_user = client.post(
        "/api/v2",
        headers={"Authorization": f"Bearer {authentification_token[:-1]}"},
        json=query_current_user,
    )

    assert response_current_user.json["data"]["currentUserResult"] == {
        "__typename": "InvalidToken",
        "message": "Invalid token. Cannot authentify.",
    }

    response_current_user_invalid_key = client.post(
        "/api/v2",
        headers={"Authorization": f"InvalidKey {authentification_token[:-1]}"},
        json=query_current_user,
    )

    assert response_current_user_invalid_key.json["data"]["currentUserResult"] == {
        "__typename": "InvalidToken",
        "message": "Invalid token. Cannot authentify.",
    }


def test_name_already_exists(client):
    user_name = get_random_string(8)

    query_signup = """
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
                    firstName
                    lastName
                    fullName
                    token
                }
                ... on UserNameAlreadyExists {
                    message
                }
            }
        }
    """

    response_signup = client.post(
        "/api/v2",
        json={
            "query": query_signup,
            "variables": {
                "userName": user_name,
                "firstName": get_random_string(8),
                "lastName": f"{get_random_string(4)} {get_random_string(5)}",
                "password": get_random_string(10),
            },
        },
    )
    assert response_signup.json["data"]["signupResult"]["__typename"] == "UserWithToken"

    response_signup_2 = client.post(
        "/api/v2",
        json={
            "query": query_signup,
            "variables": {
                "userName": user_name,
                "firstName": get_random_string(7),
                "lastName": get_random_string(10),
                "password": get_random_string(5),
            },
        },
    )
    assert response_signup_2.json["data"]["signupResult"] == {
        "__typename": "UserNameAlreadyExists",
        "message": f"Name already exists: {user_name}",
    }
