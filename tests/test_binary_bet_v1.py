from http import HTTPStatus
from typing import TYPE_CHECKING, Generator, Tuple
from unittest.mock import ANY
from uuid import uuid4

import pendulum
import pytest
from starlette.testclient import TestClient

from yak_server.cli.database import initialize_database
from yak_server.helpers.settings import get_settings

from .utils import get_random_string
from .utils.mock import MockSettings

if TYPE_CHECKING:
    from fastapi import FastAPI


# Constants
FAKE_JWT_SECRET_KEY = get_random_string(100)
JWT_EXPIRATION_TIME = 10
LOCK_DATETIME_SHIFT = pendulum.duration(minutes=10)
NAME_LENGTH = 2
FIRST_NAME_LENGTH = 6
LAST_NAME_LENGTH = 12
PASSWORD_LENGTH = 10


# Fixture for setup
@pytest.fixture(scope="module")
def login_admin(
    app: "FastAPI", monkeymodule: pytest.MonkeyPatch
) -> Generator[Tuple["FastAPI", str, str], None, None]:
    app.dependency_overrides[get_settings] = MockSettings(
        jwt_secret_key=FAKE_JWT_SECRET_KEY,
        jwt_expiration_time=JWT_EXPIRATION_TIME,
        lock_datetime_shift=LOCK_DATETIME_SHIFT,
    )

    monkeymodule.setattr(
        "yak_server.cli.database.get_settings",
        MockSettings(data_folder_relative="test_binary_bet"),
    )

    initialize_database(app)

    client = TestClient(app)

    response_signup = client.post(
        "/api/v1/users/signup",
        json={
            "name": get_random_string(NAME_LENGTH),
            "first_name": get_random_string(FIRST_NAME_LENGTH),
            "last_name": get_random_string(LAST_NAME_LENGTH),
            "password": get_random_string(PASSWORD_LENGTH),
        },
    )

    assert response_signup.status_code == HTTPStatus.CREATED
    token = response_signup.json()["result"]["token"]

    response_bets = client.get("/api/v1/bets", headers={"Authorization": f"Bearer {token}"})

    assert response_bets.status_code == HTTPStatus.OK
    bet_id = response_bets.json()["result"]["binary_bets"][0]["id"]

    yield app, token, bet_id

    app.dependency_overrides = {}


@pytest.fixture(scope="module")
def setup_app(login_admin: Tuple["FastAPI", str, str]) -> "FastAPI":
    return login_admin[0]


@pytest.fixture(scope="module")
def admin_token(login_admin: Tuple["FastAPI", str, str]) -> str:
    return login_admin[1]


@pytest.fixture(scope="module")
def bet_id(login_admin: Tuple["FastAPI", str, str]) -> str:
    return login_admin[2]


@pytest.fixture()
def setup_app_for_locked_bet(setup_app: "FastAPI") -> Generator["FastAPI", None, None]:
    original_dependencies = setup_app.dependency_overrides.copy()

    setup_app.dependency_overrides[get_settings] = MockSettings(
        lock_datetime_shift=-LOCK_DATETIME_SHIFT,
        jwt_expiration_time=JWT_EXPIRATION_TIME,
        jwt_secret_key=FAKE_JWT_SECRET_KEY,
    )

    yield setup_app

    setup_app.dependency_overrides = original_dependencies


def test_successful_binary_bet_modification(
    setup_app: "FastAPI", admin_token: str, bet_id: str
) -> None:
    client = TestClient(setup_app)

    response_modify_binary_bet = client.patch(
        f"/api/v1/binary_bets/{bet_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"is_one_won": True},
    )

    assert response_modify_binary_bet.status_code == HTTPStatus.OK
    assert response_modify_binary_bet.json() == {
        "ok": True,
        "result": {
            "phase": {"code": "GROUP", "description": "Phase de groupes", "id": ANY},
            "group": {"code": "A", "description": "Groupe A", "id": ANY},
            "binary_bet": {
                "id": ANY,
                "locked": False,
                "team1": {
                    "code": "FR",
                    "description": "France",
                    "flag": {"url": ANY},
                    "id": ANY,
                    "won": True,
                },
                "team2": {
                    "code": "GR",
                    "description": "Allemagne",
                    "flag": {"url": ANY},
                    "id": ANY,
                    "won": False,
                },
            },
        },
    }


def test_locked_binary_bet(
    setup_app_for_locked_bet: "FastAPI", admin_token: str, bet_id: str
) -> None:
    client = TestClient(setup_app_for_locked_bet)

    response_lock_bet = client.patch(
        f"/api/v1/binary_bets/{bet_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"is_one_won": True},
    )

    assert response_lock_bet.status_code == HTTPStatus.UNAUTHORIZED
    assert response_lock_bet.json() == {
        "ok": False,
        "error_code": HTTPStatus.UNAUTHORIZED,
        "description": "Cannot modify binary bet, lock date is exceeded",
    }


def test_invalid_inputs(setup_app: "FastAPI", admin_token: str, bet_id: str) -> None:
    client = TestClient(setup_app)

    # Error case : Invalid input
    response_invalid_inputs = client.patch(
        f"/api/v1/binary_bets/{bet_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"is_won": True},
    )

    assert response_invalid_inputs.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


def test_invalid_bet_id(setup_app: "FastAPI", admin_token: str) -> None:
    client = TestClient(setup_app)

    # Error case : invalid bet id
    invalid_bet_id = uuid4()

    response_with_invalid_bet_id = client.patch(
        f"/api/v1/binary_bets/{invalid_bet_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"is_one_won": True},
    )

    assert response_with_invalid_bet_id.status_code == HTTPStatus.NOT_FOUND
    assert response_with_invalid_bet_id.json() == {
        "ok": False,
        "error_code": HTTPStatus.NOT_FOUND,
        "description": f"Bet not found: {invalid_bet_id}",
    }


def test_retrieve_one_bet(setup_app: "FastAPI", admin_token: str, bet_id: str) -> None:
    client = TestClient(setup_app)

    # Success case : retrieve one binary bet
    response_binary_bet_by_id = client.get(
        f"/api/v1/binary_bets/{bet_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response_binary_bet_by_id.status_code == HTTPStatus.OK
    assert response_binary_bet_by_id.json() == {
        "ok": True,
        "result": {
            "phase": {"code": "GROUP", "description": "Phase de groupes", "id": ANY},
            "group": {"code": "A", "description": "Groupe A", "id": ANY},
            "binary_bet": {
                "id": ANY,
                "locked": False,
                "team1": {
                    "code": "FR",
                    "description": "France",
                    "flag": {"url": ANY},
                    "id": ANY,
                    "won": True,
                },
                "team2": {
                    "code": "GR",
                    "description": "Allemagne",
                    "flag": {"url": ANY},
                    "id": ANY,
                    "won": False,
                },
            },
        },
    }


def test_retrieve_with_invalid_id(setup_app: "FastAPI", admin_token: str) -> None:
    client = TestClient(setup_app)

    # Error case : retrieve binary bet with invalid id
    invalid_bet_id = uuid4()

    response_retrieve_with_invalid_bet_id = client.get(
        f"/api/v1/binary_bets/{invalid_bet_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response_retrieve_with_invalid_bet_id.status_code == HTTPStatus.NOT_FOUND
    assert response_retrieve_with_invalid_bet_id.json() == {
        "ok": False,
        "error_code": HTTPStatus.NOT_FOUND,
        "description": f"Bet not found: {invalid_bet_id}",
    }


def test_modify_team1_id(setup_app: "FastAPI", admin_token: str, bet_id: str) -> None:
    client = TestClient(setup_app)

    # Success case : Modify team1 id by setting it to None
    response_change_team1_to_none = client.patch(
        f"/api/v1/binary_bets/{bet_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"team1": {"id": None}},
    )

    assert response_change_team1_to_none.status_code == HTTPStatus.OK
    assert response_change_team1_to_none.json()["result"]["binary_bet"] == {
        "id": bet_id,
        "locked": False,
        "team1": None,
        "team2": {
            "id": ANY,
            "code": "GR",
            "description": "Allemagne",
            "flag": ANY,
            "won": False,
        },
    }


def test_modify_team2_id(setup_app: "FastAPI", admin_token: str, bet_id: str) -> None:
    client = TestClient(setup_app)

    # Success case : Change team2
    response_all_teams = client.get("/api/v1/teams")

    team_spain = [
        team for team in response_all_teams.json()["result"]["teams"] if team["code"] == "ES"
    ]

    assert len(team_spain) == 1

    team_spain = team_spain[0]["id"]

    response_change_team2 = client.patch(
        f"/api/v1/binary_bets/{bet_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"team2": {"id": team_spain}},
    )

    assert response_change_team2.status_code == HTTPStatus.OK
    assert response_change_team2.json()["result"]["binary_bet"] == {
        "id": ANY,
        "locked": False,
        "team1": None,
        "team2": {
            "id": team_spain,
            "code": "ES",
            "description": "Espagne",
            "flag": ANY,
            "won": False,
        },
    }


def test_invalid_team_id(setup_app: "FastAPI", admin_token: str, bet_id: str) -> None:
    client = TestClient(setup_app)

    invalid_team_id = str(uuid4())

    response_invalid_team1_id = client.patch(
        f"/api/v1/binary_bets/{bet_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"team1": {"id": invalid_team_id}},
    )

    assert response_invalid_team1_id.status_code == HTTPStatus.NOT_FOUND
    assert response_invalid_team1_id.json()["description"] == f"Team not found: {invalid_team_id}"

    response_invalid_team2_id = client.patch(
        f"/api/v1/binary_bets/{bet_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"team2": {"id": invalid_team_id}},
    )

    assert response_invalid_team2_id.status_code == HTTPStatus.NOT_FOUND
    assert response_invalid_team2_id.json()["description"] == f"Team not found: {invalid_team_id}"
