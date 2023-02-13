from .test_utils import get_random_string


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
    assert response_signup.json["data"]["signupResult"]["__typename"] == "UserWithToken"
    assert response_signup.json["data"]["signupResult"]["firstName"] == first_name
    assert response_signup.json["data"]["signupResult"]["lastName"] == last_name
    assert response_signup.json["data"]["signupResult"]["fullName"] == f"{first_name} {last_name}"

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
        headers=[("Authorization", f"Bearer {authentification_token}")],
        json=query_current_user,
    )

    assert response_current_user.json["data"]["currentUserResult"]["__typename"] == "User"

    # invalidate authentification token and check currentUser query
    # send InvalidToken response
    authentification_token = authentification_token[:-1]

    response_current_user = client.post(
        "/api/v2",
        headers=[("Authorization", f"Bearer {authentification_token}")],
        json=query_current_user,
    )

    assert response_current_user.json["data"]["currentUserResult"]["__typename"] == "InvalidToken"
    assert (
        response_current_user.json["data"]["currentUserResult"]["message"]
        == "Invalid token. Cannot authentify."
    )
