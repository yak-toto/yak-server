from http import HTTPStatus
from typing import TYPE_CHECKING
from unittest.mock import ANY

from starlette.testclient import TestClient

from testing.mock import MockSettings
from testing.util import get_random_string
from yak_server.helpers.settings import get_settings

if TYPE_CHECKING:
    from fastapi import FastAPI


def test_valid_auth(app_with_valid_jwt_config: "FastAPI") -> None:
    client = TestClient(app_with_valid_jwt_config)

    user_name = get_random_string(6)
    first_name = get_random_string(6)
    last_name = get_random_string(6)
    password = get_random_string(8)

    # signup test
    response_signup = client.post(
        "/api/v1/users/signup",
        json={
            "name": user_name,
            "first_name": first_name,
            "last_name": last_name,
            "password": password,
        },
    )
    assert response_signup.status_code == HTTPStatus.CREATED
    assert response_signup.json() == {
        "ok": True,
        "result": {"id": ANY, "name": user_name, "token": ANY},
    }

    # login test
    response_login = client.post(
        "/api/v1/users/login",
        json={"name": user_name, "password": password},
    )
    assert response_login.status_code == HTTPStatus.CREATED
    assert response_login.json() == {
        "ok": True,
        "result": {"id": ANY, "name": user_name, "token": ANY},
    }

    auth_token = response_login.json()["result"]["token"]

    # current user tests
    response_current_user = client.get(
        "/api/v1/users/current",
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    assert response_current_user.status_code == HTTPStatus.OK
    assert response_current_user.json() == {
        "ok": True,
        "result": {"id": ANY, "name": user_name},
    }


def test_double_signup(app_with_valid_jwt_config: "FastAPI") -> None:
    client = TestClient(app_with_valid_jwt_config)

    user_name = get_random_string(6)
    first_name = get_random_string(10)
    last_name = get_random_string(11)
    password = get_random_string(15)

    # signup test
    response_signup = client.post(
        "/api/v1/users/signup",
        json={
            "name": user_name,
            "first_name": first_name,
            "last_name": last_name,
            "password": password,
        },
    )
    assert response_signup.status_code == HTTPStatus.CREATED
    assert response_signup.json() == {
        "ok": True,
        "result": {"id": ANY, "name": user_name, "token": ANY},
    }

    # Try to signup with the same user name
    response_second_signup = client.post(
        "/api/v1/users/signup",
        json={
            "name": user_name,
            "first_name": get_random_string(10),
            "last_name": get_random_string(12),
            "password": get_random_string(8),
        },
    )
    assert response_second_signup.status_code == HTTPStatus.UNAUTHORIZED
    assert response_second_signup.json() == {
        "ok": False,
        "error_code": HTTPStatus.UNAUTHORIZED,
        "description": f"Name already exists: {user_name}",
    }


def test_login_wrong_name(app_with_valid_jwt_config: "FastAPI") -> None:
    client = TestClient(app_with_valid_jwt_config)

    response_login = client.post(
        "/api/v1/users/login",
        json={
            "name": get_random_string(15),
            "password": get_random_string(12),
        },
    )

    assert response_login.status_code == HTTPStatus.UNAUTHORIZED
    assert response_login.json() == {
        "ok": False,
        "error_code": HTTPStatus.UNAUTHORIZED,
        "description": "Invalid credentials",
    }


def test_login_wrong_password(app_with_valid_jwt_config: "FastAPI") -> None:
    client = TestClient(app_with_valid_jwt_config)

    user_name = get_random_string(6)

    response_signup = client.post(
        "/api/v1/users/signup",
        json={
            "name": user_name,
            "first_name": get_random_string(10),
            "last_name": get_random_string(11),
            "password": get_random_string(12),
        },
    )

    assert response_signup.status_code == HTTPStatus.CREATED

    response_login = client.post(
        "/api/v1/users/login",
        json={"name": user_name, "password": get_random_string(12)},
    )

    assert response_login.status_code == HTTPStatus.UNAUTHORIZED
    assert response_login.json() == {
        "ok": False,
        "error_code": HTTPStatus.UNAUTHORIZED,
        "description": "Invalid credentials",
    }


def test_invalid_token(app_with_valid_jwt_config: "FastAPI") -> None:
    client = TestClient(app_with_valid_jwt_config)

    response_signup = client.post(
        "/api/v1/users/signup",
        json={
            "name": get_random_string(6),
            "first_name": get_random_string(2),
            "last_name": get_random_string(8),
            "password": get_random_string(8),
        },
    )

    auth_token = response_signup.json()["result"]["token"]

    response_get_all_bets = client.get(
        "/api/v1/bets",
        headers={"Authorization": f"Bear {auth_token}"},
    )

    assert response_get_all_bets.json() == {
        "ok": False,
        "error_code": HTTPStatus.UNAUTHORIZED,
        "description": "Invalid token, authentication required",
    }

    response_get_all_bets_with_cropped_token = client.get(
        "/api/v1/bets",
        headers={"Authorization": f"Bearer {auth_token[:17]}{auth_token[12:]}"},
    )

    assert response_get_all_bets_with_cropped_token.status_code == HTTPStatus.UNAUTHORIZED
    assert response_get_all_bets_with_cropped_token.json() == {
        "ok": False,
        "error_code": HTTPStatus.UNAUTHORIZED,
        "description": "Invalid token, authentication required",
    }


def test_expired_token(app: "FastAPI", client: "TestClient") -> None:
    fake_jwt_secret_key = get_random_string(15)

    app.dependency_overrides[get_settings] = MockSettings(
        jwt_expiration_time=0,
        jwt_secret_key=fake_jwt_secret_key,
    )

    user_name = get_random_string(6)
    password = get_random_string(15)

    response_signup = client.post(
        "/api/v1/users/signup",
        json={
            "name": user_name,
            "first_name": get_random_string(2),
            "last_name": get_random_string(8),
            "password": password,
        },
    )

    assert response_signup.status_code == HTTPStatus.CREATED

    auth_token = response_signup.json()["result"]["token"]

    response_current_user = client.get(
        "/api/v1/users/current",
        headers={"Authorization": f"Bearer {auth_token}"},
    )

    assert response_current_user.status_code == HTTPStatus.UNAUTHORIZED
    assert response_current_user.json() == {
        "ok": False,
        "error_code": HTTPStatus.UNAUTHORIZED,
        "description": "Expired token, re-authentication required",
    }


def test_invalid_signup_body(client: "TestClient") -> None:
    name = get_random_string(10)
    first_name = get_random_string(12)
    last_name = get_random_string(6)
    password = get_random_string(5)

    # Try to signup with invalid body
    response_signup = client.post(
        "/api/v1/users/signup",
        json={
            "name": name,
            "first_name": first_name,
            "last_name": last_name,
            "passwor": password,
        },
    )

    assert response_signup.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
    assert response_signup.json() == {
        "ok": False,
        "error_code": HTTPStatus.UNPROCESSABLE_ENTITY,
        "description": [
            {
                "type": "missing",
                "loc": ["body", "password"],
                "msg": "Field required",
                "input": {
                    "name": name,
                    "first_name": first_name,
                    "last_name": last_name,
                    "passwor": password,
                },
            },
            {
                "type": "extra_forbidden",
                "loc": ["body", "passwor"],
                "msg": "Extra inputs are not permitted",
                "input": password,
            },
        ],
    }


def test_invalid_login_body(client: "TestClient") -> None:
    user_name = get_random_string(6)
    password = get_random_string(10)

    response_login = client.post(
        "/api/v1/users/login",
        json={
            "nme": user_name,
            "password": password,
        },
    )

    assert response_login.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
    assert response_login.json() == {
        "ok": False,
        "error_code": HTTPStatus.UNPROCESSABLE_ENTITY,
        "description": [
            {
                "type": "missing",
                "loc": ["body", "name"],
                "msg": "Field required",
                "input": {"nme": user_name, "password": password},
            },
            {
                "type": "extra_forbidden",
                "loc": ["body", "nme"],
                "msg": "Extra inputs are not permitted",
                "input": user_name,
            },
        ],
    }


def test_non_compliant_password(client: "TestClient") -> None:
    response_signup = client.post(
        "/api/v1/users/signup",
        json={
            "name": get_random_string(2),
            "first_name": get_random_string(2),
            "last_name": get_random_string(8),
            "password": get_random_string(6),
        },
    )

    assert response_signup.status_code == HTTPStatus.BAD_REQUEST
    assert response_signup.json() == {
        "ok": False,
        "error_code": HTTPStatus.BAD_REQUEST,
        "description": (
            "Unsatisfied password requirements. Password is too short. Minimum size is 8."
        ),
    }
