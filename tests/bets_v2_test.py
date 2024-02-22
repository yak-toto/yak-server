from typing import TYPE_CHECKING
from unittest.mock import ANY
from uuid import uuid4

from starlette.testclient import TestClient

from testing.mock import MockSettings
from testing.util import get_random_string
from yak_server.cli.database import initialize_database

if TYPE_CHECKING:
    import pytest
    from fastapi import FastAPI


def test_bets(app_with_lock_datetime_in_past: "FastAPI", monkeypatch: "pytest.MonkeyPatch") -> None:
    client = TestClient(app_with_lock_datetime_in_past)

    monkeypatch.setattr(
        "yak_server.cli.database.get_settings",
        MockSettings(data_folder_relative="test_modify_bet_v2"),
    )

    initialize_database(app_with_lock_datetime_in_past)

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

    assert response_signup.json()["data"]["signupResult"]["__typename"] == "UserWithToken"
    authentication_token = response_signup.json()["data"]["signupResult"]["token"]

    score_bet_ids = [
        bet["id"] for bet in response_signup.json()["data"]["signupResult"]["scoreBets"]
    ]

    query_score_bet = """
        query getScoreBet($scoreBetId: UUID!) {
            scoreBetResult(id: $scoreBetId) {
                __typename
                ... on ScoreBet {
                    id
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
        headers={"Authorization": f"Bearer {authentication_token}"},
        json={"query": query_score_bet, "variables": {"scoreBetId": score_bet_ids[0]}},
    )

    assert response_score_bet.json() == {
        "data": {
            "scoreBetResult": {
                "__typename": "ScoreBet",
                "id": ANY,
                "locked": True,
                "group": {"description": "Groupe A", "id": ANY},
                "team1": {"description": "Croatie", "score": None},
                "team2": {"description": "Finlande", "score": None},
            },
        },
    }

    # Error case : Bet with invalid id
    invalid_bet_id = str(uuid4())

    response_score_bet_with_invalid_id = client.post(
        "/api/v2",
        headers={"Authorization": f"Bearer {authentication_token}"},
        json={"query": query_score_bet, "variables": {"scoreBetId": invalid_bet_id}},
    )

    assert response_score_bet_with_invalid_id.json() == {
        "data": {
            "scoreBetResult": {
                "__typename": "ScoreBetNotFound",
                "message": f"Score bet not found: {invalid_bet_id}",
            },
        },
    }
