from secrets import SystemRandom
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


def test_modify_score_bet(
    app_with_valid_jwt_config: "FastAPI",
    monkeypatch: "pytest.MonkeyPatch",
) -> None:
    client = TestClient(app_with_valid_jwt_config)

    monkeypatch.setattr(
        "yak_server.cli.database.get_settings",
        MockSettings(data_folder_relative="test_modify_bet_v2"),
    )
    initialize_database(app_with_valid_jwt_config)

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

    assert response_signup.json()["data"]["signupResult"]["__typename"] == "UserWithToken"
    score_bet_ids = [
        score_bet["id"] for score_bet in response_signup.json()["data"]["signupResult"]["scoreBets"]
    ]
    authentication_token = response_signup.json()["data"]["signupResult"]["token"]

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
                        id
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
        headers={"Authorization": f"Bearer {authentication_token}"},
        json={
            "query": query_modify_score_bet,
            "variables": {
                "id": score_bet_ids[0],
                "score1": score1,
                "score2": score2,
            },
        },
    )

    new_bet = response_modify_bet.json()["data"]["modifyScoreBetResult"]

    assert new_bet["__typename"] == "ScoreBet"
    assert new_bet["team1"]["score"] == score1
    assert new_bet["team2"]["score"] == score2
    assert new_bet["team1"]["flag"]["url"] == f"/api/v1/teams/{new_bet['team1']['id']}/flag"

    # Error case : check NewScoreNegative error is send back if one of score is negative
    score1 = 5
    score2 = -1

    response_modify_bet_new_score2_negative = client.post(
        "/api/v2",
        headers={"Authorization": f"Bearer {authentication_token}"},
        json={
            "query": query_modify_score_bet,
            "variables": {
                "id": score_bet_ids[0],
                "score1": score1,
                "score2": score2,
            },
        },
    )

    assert response_modify_bet_new_score2_negative.json()["data"]["modifyScoreBetResult"] == {
        "__typename": "NewScoreNegative",
        "message": f"Variable '$score2' got invalid value {score2}. Score cannot be negative.",
    }

    # Error case : check NewScoreNegative error is send back if one of score1 is negative
    score1 = -SystemRandom().randrange(2, 9)
    score2 = 0

    response_modify_bet_new_score1_negative = client.post(
        "/api/v2",
        headers={"Authorization": f"Bearer {authentication_token}"},
        json={
            "query": query_modify_score_bet,
            "variables": {
                "id": score_bet_ids[0],
                "score1": score1,
                "score2": score2,
            },
        },
    )

    assert response_modify_bet_new_score1_negative.json()["data"]["modifyScoreBetResult"] == {
        "__typename": "NewScoreNegative",
        "message": f"Variable '$score1' got invalid value {score1}. Score cannot be negative.",
    }

    # Error case : check ScoreBetNotFoundForUpdate error if score bet does not exist
    score1 = 1
    score2 = 1

    response_modify_bet_invalid_id = client.post(
        "/api/v2",
        headers={"Authorization": f"Bearer {authentication_token}"},
        json={
            "query": query_modify_score_bet,
            "variables": {
                "id": str(uuid4()),
                "score1": score1,
                "score2": score2,
            },
        },
    )

    assert response_modify_bet_invalid_id.json()["data"]["modifyScoreBetResult"] == {
        "__typename": "ScoreBetNotFoundForUpdate",
        "message": "Score bet not found. Cannot modify a resource that does not exist.",
    }

    # Error case : check locked score bet
    app_with_valid_jwt_config.dependency_overrides[get_settings] = MockSettings(
        jwt_expiration_time=10,
        jwt_secret_key=app_with_valid_jwt_config.dependency_overrides[
            get_settings
        ]().jwt_secret_key,
        lock_datetime_shift=pendulum.duration(seconds=-10),
    )

    response_modify_locked_score_bet = client.post(
        "/api/v2",
        headers={"Authorization": f"Bearer {authentication_token}"},
        json={
            "query": query_modify_score_bet,
            "variables": {
                "id": score_bet_ids[1],
                "score1": 1,
                "score2": 1,
            },
        },
    )

    assert response_modify_locked_score_bet.json() == {
        "data": {
            "modifyScoreBetResult": {
                "__typename": "LockedScoreBetError",
                "message": "Cannot modify score bet, lock date is exceeded",
            },
        },
    }
