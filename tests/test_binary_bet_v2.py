from random import choice
from uuid import uuid4

from yak_server import db
from yak_server.database.models import (
    BinaryBetModel,
    GroupModel,
    MatchModel,
    PhaseModel,
    TeamModel,
    UserModel,
)

from .test_utils import get_random_string


def test_binary_bet(client, app):
    user_name = get_random_string(10)
    password = get_random_string(30)

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
                        }
                        ... on UserNameAlreadyExists {
                            message
                        }
                    }
                }
            """,
            "variables": {
                "userName": user_name,
                "firstName": get_random_string(6),
                "lastName": get_random_string(12),
                "password": password,
            },
        },
    )

    assert response_signup.json["data"]["signupResult"]["__typename"] == "UserWithToken"

    # set one binary bet in database
    with app.app_context():
        phase = PhaseModel(index=1, code="GROUP", description="Group stage")
        db.session.add(phase)
        db.session.commit()

        group = GroupModel(phase_id=phase.id, index=1, code="A", description="Group A")
        db.session.add(group)
        db.session.commit()

        team1 = TeamModel(code="FR", description="France")
        team2 = TeamModel(code="GR", description="Germany")
        db.session.add_all([team1, team2])
        db.session.commit()

        match = MatchModel(
            index=1,
            group_id=group.id,
            team1_id=team1.id,
            team2_id=team2.id,
        )
        db.session.add(match)
        db.session.commit()

        user = UserModel.query.first()

        binary_bet = BinaryBetModel(match_id=match.id, user_id=user.id)
        db.session.add(binary_bet)
        db.session.commit()

    response_login = client.post(
        "/api/v2",
        json={
            "query": """
                mutation Root($userName: String!, $password: String!) {
                    loginResult(userName: $userName, password: $password) {
                        __typename
                        ... on UserWithToken {
                            token
                            binaryBets {
                                id
                            }
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
    token = response_login.json["data"]["loginResult"]["token"]
    bet_id = response_login.json["data"]["loginResult"]["binaryBets"][0]["id"]

    mutation_modify_binary_bet = """
        mutation Root($id: UUID!, $isOneWon: Boolean) {
            modifyBinaryBetResult(id: $id, isOneWon: $isOneWon) {
                __typename
                ... on BinaryBet {
                    id
                    group {
                        description
                        phase {
                            description
                        }
                    }
                    team1 {
                        won
                        description
                    }
                    team2 {
                        won
                        description
                    }
                }
                ... on BinaryBetNotFoundForUpdate {
                    message
                }
                ... on LockedBinaryBetError {
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

    # Success case : modify binary bet
    is_one_won = choice([True, False, None])

    response_modify_binary_bet = client.post(
        "/api/v2",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "query": mutation_modify_binary_bet,
            "variables": {"id": bet_id, "isOneWon": is_one_won},
        },
    )

    assert response_modify_binary_bet.json == {
        "data": {
            "modifyBinaryBetResult": {
                "__typename": "BinaryBet",
                "group": {"description": "Group A", "phase": {"description": "Group stage"}},
                "id": bet_id,
                "team1": {
                    "description": "France",
                    "won": None if is_one_won is None else is_one_won,
                },
                "team2": {
                    "description": "Germany",
                    "won": None if is_one_won is None else not is_one_won,
                },
            },
        },
    }

    # Error case : Modify with invalid id
    invalid_bet_id = str(uuid4())

    response_modify_binary_bet_with_invalid_id = client.post(
        "/api/v2",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "query": mutation_modify_binary_bet,
            "variables": {"id": invalid_bet_id, "isOneWon": True},
        },
    )

    assert response_modify_binary_bet_with_invalid_id.json == {
        "data": {
            "modifyBinaryBetResult": {
                "__typename": "BinaryBetNotFoundForUpdate",
                "message": "Binary bet not found. Cannot modify a ressource that does not exist.",
            },
        },
    }

    # Error case : locked binary bet
    with app.app_context():
        binary_bet = BinaryBetModel.query.filter_by(id=bet_id).first()
        binary_bet.locked = True
        db.session.commit()

    response_modify_locked_binary_bet = client.post(
        "/api/v2",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "query": mutation_modify_binary_bet,
            "variables": {"id": bet_id, "isOneWon": True},
        },
    )

    assert response_modify_locked_binary_bet.json == {
        "data": {
            "modifyBinaryBetResult": {
                "__typename": "LockedBinaryBetError",
                "message": "Cannot modify binary bet, resource is locked.",
            },
        },
    }

    with app.app_context():
        binary_bet = BinaryBetModel.query.filter_by(id=bet_id).first()
        binary_bet.locked = False
        db.session.commit()

    # Success case : Retrive one binary bet
    query_binary_bet = """
        query getBinaryBet($id: UUID!) {
            binaryBetResult(id: $id) {
                __typename
                ... on BinaryBet {
                    id
                    group {
                        description
                        phase {
                            description
                        }
                    }
                    team1 {
                        won
                        description
                    }
                    team2 {
                        won
                        description
                    }
                }
                ... on InvalidToken {
                    message
                }
                ... on ExpiredToken {
                    message
                }
                ... on BinaryBetNotFound {
                    message
                }
            }
        }
    """

    response_retrieve_binary_bet = client.post(
        "/api/v2",
        headers={"Authorization": f"Bearer {token}"},
        json={"query": query_binary_bet, "variables": {"id": bet_id}},
    )

    assert response_retrieve_binary_bet.json == {
        "data": {
            "binaryBetResult": {
                "__typename": "BinaryBet",
                "group": {"description": "Group A", "phase": {"description": "Group stage"}},
                "id": bet_id,
                "team1": {
                    "description": "France",
                    "won": None if is_one_won is None else is_one_won,
                },
                "team2": {
                    "description": "Germany",
                    "won": None if is_one_won is None else not is_one_won,
                },
            },
        },
    }

    # Error case : retrieve binary bet with invalid id
    invalid_bet_id = str(uuid4())

    response_binary_with_invalid_id = client.post(
        "/api/v2",
        headers={"Authorization": f"Bearer {token}"},
        json={"query": query_binary_bet, "variables": {"id": invalid_bet_id}},
    )

    assert response_binary_with_invalid_id.json == {
        "data": {
            "binaryBetResult": {
                "__typename": "BinaryBetNotFound",
                "message": f"Cannot find binary bet with id: {invalid_bet_id}",
            },
        },
    }
