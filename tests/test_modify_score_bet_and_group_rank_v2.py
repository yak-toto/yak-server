from datetime import datetime, timedelta
from importlib import resources
from random import randint

import pytest

from yak_server.cli.database import initialize_database

from .test_utils import get_random_string


@pytest.fixture(autouse=True)
def setup_app(app):
    testcase = "test_modify_score_bet_and_group_rank"

    # location of test data
    with resources.as_file(resources.files("tests") / testcase) as path:
        app.config["DATA_FOLDER"] = path
    old_lock_datetime = app.config["LOCK_DATETIME"]
    app.config["LOCK_DATETIME"] = str(datetime.now() + timedelta(minutes=10))

    with app.app_context():
        initialize_database(app)

    yield app

    app.config["LOCK_DATETIME"] = old_lock_datetime


def test_modify_score_bet_and_group_rank(client):
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
                "userName": get_random_string(6),
                "firstName": get_random_string(6),
                "lastName": get_random_string(6),
                "password": get_random_string(6),
            },
        },
    )

    assert response_signup.json["data"]["signupResult"]["__typename"] == "UserWithToken"
    token = response_signup.json["data"]["signupResult"]["token"]

    # Success case : Modify score bet and observe group rank update
    query_modify_score_and_group_rank = """
        mutation Root($id: UUID!, $score1: Int, $score2: Int) {
            modifyScoreBetResult(id: $id, score1: $score1, score2: $score2) {
                __typename
                ... on ScoreBet {
                    id
                    locked
                    group {
                        description
                        groupRank {
                            team {
                                description
                            }
                            won
                            drawn
                            lost
                            points
                            goalsFor
                            goalsAgainst
                            goalsDifference
                        }
                        phase {
                            description
                        }
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
            }
        }
    """

    score1 = randint(1, 7)
    score2 = randint(0, score1 - 1)

    # Apply twice the same update to check first, updates are ok and then second, that nothing
    # change
    for _ in range(2):
        response_modify_score_bet = client.post(
            "/api/v2",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "query": query_modify_score_and_group_rank,
                "variables": {
                    "id": response_signup.json["data"]["signupResult"]["scoreBets"][0]["id"],
                    "score1": score1,
                    "score2": score2,
                },
            },
        )

        group_rank = response_modify_score_bet.json["data"]["modifyScoreBetResult"]["group"][
            "groupRank"
        ]

        assert group_rank[0]["goalsFor"] == score1
        assert group_rank[0]["goalsAgainst"] == score2
        assert group_rank[3]["goalsFor"] == score2
        assert group_rank[3]["goalsAgainst"] == score1
