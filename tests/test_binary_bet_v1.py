from datetime import datetime, timedelta
from http import HTTPStatus
from unittest.mock import ANY
from uuid import uuid4

from yak_server import db
from yak_server.database.models import BinaryBetModel, GroupModel, MatchModel, PhaseModel, TeamModel

from .test_utils import get_random_string


def test_binary_bet(client, app):
    old_lock_datetime = app.config["LOCK_DATETIME"]
    app.config["LOCK_DATETIME"] = str(datetime.now() + timedelta(seconds=30))

    response_signup = client.post(
        "/api/v1/users/signup",
        json={
            "name": get_random_string(2),
            "first_name": get_random_string(6),
            "last_name": get_random_string(12),
            "password": get_random_string(10),
        },
    )

    assert response_signup.status_code == HTTPStatus.CREATED

    user_id = response_signup.json["result"]["id"]
    token = response_signup.json["result"]["token"]

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

        binary_bet = BinaryBetModel(match_id=match.id, user_id=user_id)
        db.session.add(binary_bet)
        db.session.commit()

    response_bets = client.get("/api/v1/bets", headers={"Authorization": f"Bearer {token}"})

    assert response_bets.status_code == HTTPStatus.OK

    bet_id = response_bets.json["result"]["binary_bets"][0]["id"]

    response_modify_binary_bet = client.patch(
        f"/api/v1/binary_bets/{bet_id}",
        headers={"Authorization": f"Bearer {token}"},
        json={"is_one_won": True},
    )

    assert response_modify_binary_bet.status_code == HTTPStatus.OK
    assert response_modify_binary_bet.json == {
        "ok": True,
        "result": {
            "phase": {"code": "GROUP", "description": "Group stage", "id": ANY},
            "group": {"code": "A", "description": "Group A", "id": ANY},
            "binary_bet": {
                "id": ANY,
                "index": 1,
                "locked": False,
                "match_id": ANY,
                "team1": {
                    "code": "FR",
                    "description": "France",
                    "flag": {"url": ANY},
                    "id": ANY,
                    "won": True,
                },
                "team2": {
                    "code": "GR",
                    "description": "Germany",
                    "flag": {"url": ANY},
                    "id": ANY,
                    "won": False,
                },
            },
        },
    }

    # Error case : locked bet
    app.config["LOCK_DATETIME"] = str(datetime.now() - timedelta(seconds=10))

    response_lock_bet = client.patch(
        f"/api/v1/binary_bets/{bet_id}",
        headers={"Authorization": f"Bearer {token}"},
        json={"is_one_won": True},
    )

    assert response_lock_bet.status_code == HTTPStatus.UNAUTHORIZED
    assert response_lock_bet.json == {
        "ok": False,
        "error_code": HTTPStatus.UNAUTHORIZED,
        "description": "Cannot modify bets because locked date is exceeded",
    }

    app.config["LOCK_DATETIME"] = str(datetime.now() + timedelta(seconds=30))

    # Error case : Invalid input
    response_invalid_inputs = client.patch(
        f"/api/v1/binary_bets/{bet_id}",
        headers={"Authorization": f"Bearer {token}"},
        json={"is_won": True},
    )

    assert response_invalid_inputs.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
    assert response_invalid_inputs.json == {
        "ok": False,
        "error_code": HTTPStatus.UNPROCESSABLE_ENTITY,
        "description": "'is_one_won' is a required property",
        "schema": {
            "type": "object",
            "properties": {"is_one_won": {"oneOf": [{"type": "boolean"}, {"type": "null"}]}},
            "required": ["is_one_won"],
        },
        "path": [],
    }

    # Error case : invalid bet id
    invalid_bet_id = str(uuid4())

    response_with_invalid_bet_id = client.patch(
        f"/api/v1/binary_bets/{invalid_bet_id}",
        headers={"Authorization": f"Bearer {token}"},
        json={"is_one_won": True},
    )

    assert response_with_invalid_bet_id.status_code == HTTPStatus.NOT_FOUND
    assert response_with_invalid_bet_id.json == {
        "ok": False,
        "error_code": HTTPStatus.NOT_FOUND,
        "description": f"Bet not found: {invalid_bet_id}",
    }

    # Success case : retrieve one binary bet
    response_binary_bet_by_id = client.get(
        f"/api/v1/binary_bets/{bet_id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response_binary_bet_by_id.status_code == HTTPStatus.OK
    assert response_binary_bet_by_id.json == {
        "ok": True,
        "result": {
            "phase": {"code": "GROUP", "description": "Group stage", "id": ANY},
            "group": {"code": "A", "description": "Group A", "id": ANY},
            "binary_bet": {
                "id": ANY,
                "index": 1,
                "locked": False,
                "match_id": ANY,
                "team1": {
                    "code": "FR",
                    "description": "France",
                    "flag": {"url": ANY},
                    "id": ANY,
                    "won": True,
                },
                "team2": {
                    "code": "GR",
                    "description": "Germany",
                    "flag": {"url": ANY},
                    "id": ANY,
                    "won": False,
                },
            },
        },
    }

    # Error case : retrieve binary bet with invalid id
    invalid_bet_id = str(uuid4())

    response_retrieve_with_invalid_bet_id = client.get(
        f"/api/v1/binary_bets/{invalid_bet_id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response_retrieve_with_invalid_bet_id.status_code == HTTPStatus.NOT_FOUND
    assert response_retrieve_with_invalid_bet_id.json == {
        "ok": False,
        "error_code": HTTPStatus.NOT_FOUND,
        "description": f"Bet not found: {invalid_bet_id}",
    }

    # Fallback lock datetime
    app.config["LOCK_DATETIME"] = old_lock_datetime
