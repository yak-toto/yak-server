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


def test_phase(
    app_with_lock_datetime_in_past: "FastAPI",
    monkeypatch: "pytest.MonkeyPatch",
) -> None:
    client = TestClient(app_with_lock_datetime_in_past)

    monkeypatch.setattr(
        "yak_server.cli.database.get_settings",
        MockSettings(data_folder_relative="test_matches_db"),
    )
    initialize_database(app_with_lock_datetime_in_past)

    # Signup one random user
    user_name = get_random_string(6)
    first_name = get_random_string(10)
    last_name = get_random_string(8)
    password = get_random_string(15)

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
                "firstName": first_name,
                "lastName": last_name,
                "password": password,
            },
        },
    )

    assert response_signup.json()["data"]["signupResult"]["__typename"] == "UserWithToken"

    token = response_signup.json()["data"]["signupResult"]["token"]

    # Check retrieve all phases
    response_all_phases = client.post(
        "/api/v2",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "query": """
                query {
                    allPhasesResult {
                        __typename
                        ... on Phases {
                            phases {
                                id
                                code
                                description
                                binaryBets {
                                    team1 {
                                        description
                                        won
                                    }
                                    team2 {
                                        description
                                        won
                                    }
                                }
                                scoreBets {
                                    team1 {
                                        description
                                        score
                                    }
                                    team2 {
                                        description
                                        score
                                    }
                                }
                                groups {
                                    id
                                    description
                                    code
                                    scoreBets {
                                        id
                                        locked
                                        team1 {
                                            score
                                            description
                                        }
                                        team2 {
                                            score
                                            description
                                        }
                                    }
                                    binaryBets {
                                        id
                                        locked
                                        team1 {
                                            won
                                            description
                                        }
                                        team2 {
                                            won
                                            description
                                        }
                                    }
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
        },
    )

    assert response_all_phases.json() == {
        "data": {
            "allPhasesResult": {
                "__typename": "Phases",
                "phases": [
                    {
                        "id": ANY,
                        "code": "GROUP",
                        "description": "Phase de groupes",
                        "binaryBets": [],
                        "scoreBets": [
                            {
                                "team1": {"description": "Andorre", "score": None},
                                "team2": {"description": "Brésil", "score": None},
                            },
                            {
                                "team1": {"description": "Burkina Faso", "score": None},
                                "team2": {
                                    "description": "Guatemala",
                                    "score": None,
                                },
                            },
                            {
                                "team1": {"description": "Andorre", "score": None},
                                "team2": {"description": "Burkina Faso", "score": None},
                            },
                            {
                                "team1": {"description": "Brésil", "score": None},
                                "team2": {
                                    "description": "Guatemala",
                                    "score": None,
                                },
                            },
                            {
                                "team1": {"description": "Andorre", "score": None},
                                "team2": {
                                    "description": "Guatemala",
                                    "score": None,
                                },
                            },
                            {
                                "team1": {"description": "Brésil", "score": None},
                                "team2": {"description": "Burkina Faso", "score": None},
                            },
                        ],
                        "groups": [
                            {
                                "binaryBets": [],
                                "code": "A",
                                "description": "Groupe A",
                                "id": ANY,
                                "scoreBets": [
                                    {
                                        "id": ANY,
                                        "locked": True,
                                        "team1": {"description": "Andorre", "score": None},
                                        "team2": {"description": "Brésil", "score": None},
                                    },
                                    {
                                        "id": ANY,
                                        "locked": True,
                                        "team1": {"description": "Burkina Faso", "score": None},
                                        "team2": {
                                            "description": "Guatemala",
                                            "score": None,
                                        },
                                    },
                                    {
                                        "id": ANY,
                                        "locked": True,
                                        "team1": {"description": "Andorre", "score": None},
                                        "team2": {"description": "Burkina Faso", "score": None},
                                    },
                                    {
                                        "id": ANY,
                                        "locked": True,
                                        "team1": {"description": "Brésil", "score": None},
                                        "team2": {
                                            "description": "Guatemala",
                                            "score": None,
                                        },
                                    },
                                    {
                                        "id": ANY,
                                        "locked": True,
                                        "team1": {"description": "Andorre", "score": None},
                                        "team2": {
                                            "description": "Guatemala",
                                            "score": None,
                                        },
                                    },
                                    {
                                        "id": ANY,
                                        "locked": True,
                                        "team1": {"description": "Brésil", "score": None},
                                        "team2": {"description": "Burkina Faso", "score": None},
                                    },
                                ],
                            },
                        ],
                    },
                ],
            },
        },
    }

    # Success case : Retrieve phase by id
    query_phase_by_id = """query Root($phaseId: UUID!) {
        phaseByIdResult(id: $phaseId) {
            __typename
            ... on Phase {
                id
                code
                description
            }
            ... on InvalidToken {
                message
            }
            ... on ExpiredToken {
                message
            }
            ... on PhaseByIdNotFound {
                message
            }
        }
    }
    """

    phase_id = response_all_phases.json()["data"]["allPhasesResult"]["phases"][0]["id"]

    response_phase_by_id = client.post(
        "/api/v2",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "query": query_phase_by_id,
            "variables": {"phaseId": phase_id},
        },
    )

    assert response_phase_by_id.json() == {
        "data": {
            "phaseByIdResult": {
                "__typename": "Phase",
                "id": phase_id,
                "code": "GROUP",
                "description": "Phase de groupes",
            },
        },
    }

    # Error case : phase with invalid id
    invalid_phase_id = str(uuid4())

    response_phase_with_invalid_id = client.post(
        "/api/v2",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "query": query_phase_by_id,
            "variables": {"phaseId": invalid_phase_id},
        },
    )

    assert response_phase_with_invalid_id.json() == {
        "data": {
            "phaseByIdResult": {
                "__typename": "PhaseByIdNotFound",
                "message": f"Phase not found: {invalid_phase_id}",
            },
        },
    }

    # Success case : Fetch phase by code
    query_phase_by_code = """query Root($phaseCode: String!) {
        phaseByCodeResult(code: $phaseCode) {
            __typename
            ... on Phase {
                id
                code
                description
            }
            ... on InvalidToken {
                message
            }
            ... on ExpiredToken {
                message
            }
            ... on PhaseByCodeNotFound {
                message
            }
        }
    }
    """

    phase_code = response_phase_by_id.json()["data"]["phaseByIdResult"]["code"]

    response_phase_by_code = client.post(
        "/api/v2",
        headers={"Authorization": f"Bearer {token}"},
        json={"query": query_phase_by_code, "variables": {"phaseCode": phase_code}},
    )

    assert response_phase_by_code.json() == {
        "data": {
            "phaseByCodeResult": {
                "__typename": "Phase",
                "id": phase_id,
                "code": phase_code,
                "description": "Phase de groupes",
            },
        },
    }

    # Error case : Phase with invalid code
    invalid_phase_code = get_random_string(6)

    response_phase_with_invalid_code = client.post(
        "/api/v2",
        headers={"Authorization": f"Bearer {token}"},
        json={"query": query_phase_by_code, "variables": {"phaseCode": invalid_phase_code}},
    )

    assert response_phase_with_invalid_code.json() == {
        "data": {
            "phaseByCodeResult": {
                "__typename": "PhaseByCodeNotFound",
                "message": f"Phase not found: {invalid_phase_code}",
            },
        },
    }
