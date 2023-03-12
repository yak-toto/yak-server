from importlib import resources
from unittest.mock import ANY
from uuid import uuid4

import pytest

from yak_server.cli.database import initialize_database

from .test_utils import get_random_string


@pytest.fixture(autouse=True)
def setup_app(app):
    testcase = "test_modify_bet_v2"

    with resources.as_file(resources.files("tests") / testcase) as path:
        app.config["DATA_FOLDER"] = path

    with app.app_context():
        initialize_database(app)

    return app


def test_bets(client):
    user_name = get_random_string(10)
    first_name = get_random_string(5)
    last_name = get_random_string(8)
    password = get_random_string(15)

    query_signup = """
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
                    scoreBets {
                        id
                    }
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
                "firstName": first_name,
                "lastName": last_name,
                "password": password,
            },
        },
    )

    assert response_signup.json["data"]["signupResult"]["__typename"] == "UserWithToken"
    authentification_token = response_signup.json["data"]["signupResult"]["token"]

    score_bet_ids = [bet["id"] for bet in response_signup.json["data"]["signupResult"]["scoreBets"]]

    query_score_bet = """
        query getScoreBet($scoreBetId: UUID!) {
            scoreBetResult(id: $scoreBetId) {
                __typename
                ... on ScoreBet {
                    id
                    index
                    locked
                    group {
                        id
                        description
                    }
                    team1 {
                        score
                        description
                    }
                    team2 {
                        score
                        description
                    }
                }
                ... on InvalidToken {
                    message
                }
                ... on ExpiredToken {
                    message
                }
                ... on ScoreBetNotFound {
                    message
                }
            }
        }
    """

    # Success case : Retrieve one score bet
    response_score_bet = client.post(
        "/api/v2",
        headers={"Authorization": f"Bearer {authentification_token}"},
        json={"query": query_score_bet, "variables": {"scoreBetId": score_bet_ids[0]}},
    )

    assert response_score_bet.json == {
        "data": {
            "scoreBetResult": {
                "__typename": "ScoreBet",
                "id": ANY,
                "index": 1,
                "locked": True,
                "group": {"description": "Groupe A", "id": ANY},
                "team1": {"description": "Crotia", "score": None},
                "team2": {"description": "Finland", "score": None},
            },
        },
    }

    # Error case : Bet with invalid id
    invalid_bet_id = str(uuid4())

    response_score_bet_with_invalid_id = client.post(
        "/api/v2",
        headers={"Authorization": f"Bearer {authentification_token}"},
        json={"query": query_score_bet, "variables": {"scoreBetId": invalid_bet_id}},
    )

    assert response_score_bet_with_invalid_id.json == {
        "data": {
            "scoreBetResult": {
                "__typename": "ScoreBetNotFound",
                "message": f"Cannot find score bet with id: {invalid_bet_id}",
            },
        },
    }
