from importlib import resources
from random import randint
from uuid import uuid4

from yak_server import db
from yak_server.cli.database import initialize_database
from yak_server.database.models import ScoreBetModel

from .test_utils import get_random_string


def test_modify_score_bet(app, client):
    testcase = "test_modify_bet_v2"

    # location of test data
    with resources.as_file(resources.files("tests") / testcase) as path:
        app.config["DATA_FOLDER"] = path

    with app.app_context():
        initialize_database(app)

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
                            scoreBets {
                                id
                            }
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
    score_bet_ids = [
        score_bet["id"] for score_bet in response_signup.json["data"]["signupResult"]["scoreBets"]
    ]
    authentification_token = response_signup.json["data"]["signupResult"]["token"]

    # Success case : check update is OK
    score1 = 4
    score2 = 4

    query_modify_score_bet = """
        mutation ModifyScoreBet($id: UUID!, $score1: Int, $score2: Int) {
            modifyScoreBetResult(id: $id, score1: $score1, score2: $score2) {
                __typename
                ... on ScoreBet {
                    id
                    team1 {
                        description
                        score
                        flag {
                            url
                        }
                    }
                    team2 {
                        description
                        score
                        flag {
                            url
                        }
                    }
                    group {
                        id
                        description
                        phase {
                            description
                        }
                    }
                }
                ... on ScoreBetNotFoundForUpdate {
                    message
                }
                ... on LockedScoreBetError {
                    message
                }
                ... on InvalidToken {
                    message
                }
                ... on ExpiredToken {
                    message
                }
                ... on NewScoreNegative {
                    message
                }
            }
        }
    """

    response_modify_bet = client.post(
        "/api/v2",
        headers={"Authorization": f"Bearer {authentification_token}"},
        json={
            "query": query_modify_score_bet,
            "variables": {
                "id": score_bet_ids[0],
                "score1": score1,
                "score2": score2,
            },
        },
    )

    assert response_modify_bet.json["data"]["modifyScoreBetResult"]["__typename"] == "ScoreBet"
    assert response_modify_bet.json["data"]["modifyScoreBetResult"]["team1"]["score"] == score1
    assert response_modify_bet.json["data"]["modifyScoreBetResult"]["team2"]["score"] == score2
    assert (
        response_modify_bet.json["data"]["modifyScoreBetResult"]["team1"]["flag"]["url"]
        == "https://fake-team-flag_croatia.com"
    )
    assert response_modify_bet.json["data"]["modifyScoreBetResult"]["team2"]["score"] == score2

    # Error case : check NewScoreNegative error is send back if one of score is negative
    score1 = 5
    score2 = -1

    response_modify_bet_new_score2_negative = client.post(
        "/api/v2",
        headers={"Authorization": f"Bearer {authentification_token}"},
        json={
            "query": query_modify_score_bet,
            "variables": {
                "id": score_bet_ids[0],
                "score1": score1,
                "score2": score2,
            },
        },
    )

    assert response_modify_bet_new_score2_negative.json["data"]["modifyScoreBetResult"] == {
        "__typename": "NewScoreNegative",
        "message": f"Variable '$score2' got invalid value {score2}. Score cannot be negative.",
    }

    # Error case : check NewScoreNegative error is send back if one of score1 is negative
    score1 = randint(-8, -1)
    score2 = 0

    response_modify_bet_new_score1_negative = client.post(
        "/api/v2",
        headers={"Authorization": f"Bearer {authentification_token}"},
        json={
            "query": query_modify_score_bet,
            "variables": {
                "id": score_bet_ids[0],
                "score1": score1,
                "score2": score2,
            },
        },
    )

    assert response_modify_bet_new_score1_negative.json["data"]["modifyScoreBetResult"] == {
        "__typename": "NewScoreNegative",
        "message": f"Variable '$score1' got invalid value {score1}. Score cannot be negative.",
    }

    # Error case : check locked score bet
    with app.app_context():
        score_bet = ScoreBetModel.query.filter_by(id=score_bet_ids[1]).first()
        score_bet.locked = True
        db.session.commit()

    response_modify_locked_score_bet = client.post(
        "/api/v2",
        headers={"Authorization": f"Bearer {authentification_token}"},
        json={
            "query": query_modify_score_bet,
            "variables": {
                "id": score_bet_ids[1],
                "score1": 1,
                "score2": 1,
            },
        },
    )

    assert response_modify_locked_score_bet.json == {
        "data": {
            "modifyScoreBetResult": {
                "__typename": "LockedScoreBetError",
                "message": "Cannot modify score bet, resource is locked.",
            },
        },
    }

    with app.app_context():
        score_bet = ScoreBetModel.query.filter_by(id=score_bet_ids[1]).first()
        score_bet.locked = False
        db.session.commit()

    # Error case : check ScoreBetNotFoundForUpdate error if score bet does not exist
    score1 = 1
    score2 = 1

    response_modify_bet_invalid_id = client.post(
        "/api/v2",
        headers={"Authorization": f"Bearer {authentification_token}"},
        json={
            "query": query_modify_score_bet,
            "variables": {
                "id": str(uuid4()),
                "score1": score1,
                "score2": score2,
            },
        },
    )

    assert response_modify_bet_invalid_id.json["data"]["modifyScoreBetResult"] == {
        "__typename": "ScoreBetNotFoundForUpdate",
        "message": "Score bet not found. Cannot modify a ressource that does not exist.",
    }
