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


def test_group_rank(
    app_with_valid_jwt_config: "FastAPI",
    monkeypatch: "pytest.MonkeyPatch",
) -> None:
    client = TestClient(app_with_valid_jwt_config)

    monkeypatch.setattr(
        "yak_server.cli.database.get_settings",
        MockSettings(data_folder_relative="test_compute_points_v1"),
    )
    initialize_database(app_with_valid_jwt_config)

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
                "userName": get_random_string(6),
                "firstName": get_random_string(10),
                "lastName": get_random_string(10),
                "password": get_random_string(10),
            },
        },
    )

    assert response_signup.json()["data"]["signupResult"]["__typename"] == "UserWithToken"

    token = response_signup.json()["data"]["signupResult"]["token"]

    query_modify_score_bet = """
        mutation Root($id: UUID!, $score1: Int!, $score2: Int!) {
            modifyScoreBetResult(id: $id, score1: $score1, score2: $score2) {
                __typename
                ... on ScoreBet {
                    id
                }
                ... on ScoreBetNotFoundForUpdate {
                    message
                }
                ... on LockedScoreBetError {
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

    # Modify score bet
    new_scores = [(5, 1), (0, 0), (1, 2)]

    for bet, new_score in zip(
        response_signup.json()["data"]["signupResult"]["scoreBets"],
        new_scores,
    ):
        response_patch_bet = client.post(
            "/api/v2",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "query": query_modify_score_bet,
                "variables": {
                    "id": bet["id"],
                    "score1": new_score[0],
                    "score2": new_score[1],
                },
            },
        )

        assert response_patch_bet.json()["data"]["modifyScoreBetResult"]["__typename"] == "ScoreBet"

    query_group_rank = """
        query Root($code: String!) {
            groupRankByCodeResult(code: $code) {
                __typename
                ... on GroupRank {
                    group {
                        id
                        description
                    }
                    groupRank {
                        team {
                            description
                            code
                            id
                            flag {
                                url
                            }
                        }
                        played
                        won
                        drawn
                        lost
                        goalsFor
                        goalsAgainst
                        goalsDifference
                        points
                    }
                }
                ... on InvalidToken {
                    message
                }
                ... on ExpiredToken {
                    message
                }
                ... on GroupByCodeNotFound {
                    message
                }
            }
        }
    """

    # Success case : Fetch group rank and check updates
    response_group_rank_by_code = client.post(
        "/api/v2",
        json={"query": query_group_rank, "variables": {"code": "A"}},
        headers={"Authorization": f"Bearer {token}"},
    )

    result_group_rank = {
        "__typename": "GroupRank",
        "group": {"id": ANY, "description": "Groupe A"},
        "groupRank": [
            {
                "drawn": 1,
                "goalsAgainst": 1,
                "goalsDifference": 4,
                "goalsFor": 5,
                "lost": 0,
                "played": 2,
                "points": 4,
                "team": {
                    "description": "France",
                    "code": "FR",
                    "id": ANY,
                    "flag": {"url": ANY},
                },
                "won": 1,
            },
            {
                "drawn": 1,
                "goalsAgainst": 1,
                "goalsDifference": 1,
                "goalsFor": 2,
                "lost": 0,
                "played": 2,
                "points": 4,
                "team": {
                    "description": "Île de Man",
                    "code": "IM",
                    "id": ANY,
                    "flag": {"url": ANY},
                },
                "won": 1,
            },
            {
                "drawn": 0,
                "goalsAgainst": 7,
                "goalsDifference": -5,
                "goalsFor": 2,
                "lost": 2,
                "played": 2,
                "points": 0,
                "team": {
                    "description": "Irlande",
                    "code": "IE",
                    "id": ANY,
                    "flag": {"url": ANY},
                },
                "won": 0,
            },
        ],
    }

    assert response_group_rank_by_code.json()["data"] == {
        "groupRankByCodeResult": result_group_rank,
    }

    # Error case : Retrieve group rank with invalid group code
    group_id = response_group_rank_by_code.json()["data"]["groupRankByCodeResult"]["group"]["id"]

    invalid_group_code = "B"

    response_group_rank_with_invalid_code = client.post(
        "/api/v2",
        json={"query": query_group_rank, "variables": {"code": invalid_group_code}},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response_group_rank_with_invalid_code.json()["data"] == {
        "groupRankByCodeResult": {
            "__typename": "GroupByCodeNotFound",
            "message": f"Group not found: {invalid_group_code}",
        },
    }

    # Error case : Retrieve group rank with invalid token
    response_group_rank_with_auth_error = client.post(
        "/api/v2",
        json={"query": query_group_rank, "variables": {"code": "A"}},
        headers={"Authorization": f"Bearer {token[:-1]}"},
    )

    assert response_group_rank_with_auth_error.json()["data"] == {
        "groupRankByCodeResult": {
            "__typename": "InvalidToken",
            "message": "Invalid token, authentication required",
        },
    }

    query_group_rank_by_id = """
        query Root($id: UUID!) {
            groupRankByIdResult(id: $id) {
                __typename
                ... on GroupRank {
                    group {
                        id
                        description
                    }
                    groupRank {
                        team {
                            description
                            code
                            id
                            flag {
                                url
                            }
                        }
                        played
                        won
                        drawn
                        lost
                        goalsFor
                        goalsAgainst
                        goalsDifference
                        points
                    }
                }
                ... on InvalidToken {
                    message
                }
                ... on ExpiredToken {
                    message
                }
                ... on GroupByIdNotFound {
                    message
                }
            }
        }
    """

    # Success case : retrieve group rank with group id
    response_group_rank_by_id = client.post(
        "/api/v2",
        json={"query": query_group_rank_by_id, "variables": {"id": group_id}},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response_group_rank_by_id.json()["data"] == {"groupRankByIdResult": result_group_rank}

    # Error case : invalid authentication
    response_group_rank_by_id_auth_error = client.post(
        "/api/v2",
        json={"query": query_group_rank_by_id, "variables": {"id": group_id}},
        headers={"Authorization": f"Bearer {token[:-1]}"},
    )

    assert response_group_rank_by_id_auth_error.json()["data"] == {
        "groupRankByIdResult": {
            "__typename": "InvalidToken",
            "message": "Invalid token, authentication required",
        },
    }

    # Error case : retrieve group rank with invalid id
    invalid_id = str(uuid4())

    response_group_rank_with_invalid_id = client.post(
        "/api/v2",
        json={"query": query_group_rank_by_id, "variables": {"id": invalid_id}},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response_group_rank_with_invalid_id.json()["data"] == {
        "groupRankByIdResult": {
            "__typename": "GroupByIdNotFound",
            "message": f"Group not found: {invalid_id}",
        },
    }

    # Modify score bet and check group rank by id updates
    response_modify_score_bet = client.post(
        "/api/v2",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "query": query_modify_score_bet,
            "variables": {
                "id": bet["id"],
                "score1": 4,
                "score2": 3,
            },
        },
    )

    assert (
        response_modify_score_bet.json()["data"]["modifyScoreBetResult"]["__typename"] == "ScoreBet"
    )

    response_retrieve_group_rank_by_id = client.post(
        "/api/v2",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "query": query_group_rank_by_id,
            "variables": {
                "id": group_id,
            },
        },
    )

    group_rank_result = {
        "__typename": "GroupRank",
        "group": {"description": "Groupe A", "id": group_id},
        "groupRank": [
            {
                "team": ANY,
                "played": 2,
                "won": 1,
                "drawn": 1,
                "lost": 0,
                "goalsFor": 5,
                "goalsAgainst": 1,
                "goalsDifference": 4,
                "points": 4,
            },
            {
                "team": ANY,
                "played": 2,
                "won": 1,
                "drawn": 0,
                "lost": 1,
                "goalsFor": 5,
                "goalsAgainst": 8,
                "goalsDifference": -3,
                "points": 3,
            },
            {
                "team": ANY,
                "played": 2,
                "won": 0,
                "drawn": 1,
                "lost": 1,
                "goalsFor": 3,
                "goalsAgainst": 4,
                "goalsDifference": -1,
                "points": 1,
            },
        ],
    }

    assert response_retrieve_group_rank_by_id.json()["data"] == {
        "groupRankByIdResult": group_rank_result,
    }

    # Success case : No recomputation for group rank
    response_retrieve_group_rank_by_code = client.post(
        "/api/v2",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "query": query_group_rank,
            "variables": {
                "code": "A",
            },
        },
    )

    assert response_retrieve_group_rank_by_code.json()["data"] == {
        "groupRankByCodeResult": group_rank_result,
    }
