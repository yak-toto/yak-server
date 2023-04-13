from http import HTTPStatus
from unittest.mock import ANY

import pytest

from .utils import get_random_string


def test_valid_auth(client):
    user_name = get_random_string(6)
    first_name = get_random_string(6)
    last_name = get_random_string(6)
    password = get_random_string(6)

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
    assert response_signup.json == {
        "ok": True,
        "result": {"id": ANY, "name": user_name, "token": ANY},
    }

    # login test
    response_login = client.post(
        "/api/v1/users/login",
        json={"name": user_name, "password": password},
    )
    assert response_login.status_code == HTTPStatus.CREATED
    assert response_login.json == {
        "ok": True,
        "result": {"id": ANY, "name": user_name, "token": ANY},
    }

    auth_token = response_login.json["result"]["token"]

    # current user tests
    response_current_user = client.get(
        "/api/v1/current_user",
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    assert response_current_user.status_code == HTTPStatus.OK
    assert response_current_user.json == {
        "ok": True,
        "result": {"id": ANY, "name": user_name},
    }


def test_double_signup(client):
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
    assert response_signup.json == {
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
            "password": get_random_string(6),
        },
    )
    assert response_second_signup.status_code == HTTPStatus.UNAUTHORIZED
    assert response_second_signup.json == {
        "ok": False,
        "error_code": HTTPStatus.UNAUTHORIZED,
        "description": f"Name already exists: {user_name}",
    }


def test_login_wrong_password(client):
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
    assert response_login.json == {
        "ok": False,
        "error_code": HTTPStatus.UNAUTHORIZED,
        "description": "Invalid credentials",
    }


def test_invalid_token(client):
    response_signup = client.post(
        "/api/v1/users/signup",
        json={
            "name": get_random_string(6),
            "first_name": get_random_string(2),
            "last_name": get_random_string(8),
            "password": get_random_string(8),
        },
    )

    auth_token = response_signup.json["result"]["token"]

    response_get_all_bets = client.get(
        "/api/v1/bets",
        headers={"Authorization": f"Bear {auth_token}"},
    )

    assert response_get_all_bets.status_code == HTTPStatus.UNAUTHORIZED
    assert response_get_all_bets.json == {
        "ok": False,
        "error_code": HTTPStatus.UNAUTHORIZED,
        "description": "Invalid token, authentication required",
    }

    response_get_all_bets_with_cropped_token = client.get(
        "/api/v1/bets",
        headers={"Authorization": f"Bearer {auth_token[:17]}{auth_token[12:]}"},
    )

    assert response_get_all_bets_with_cropped_token.status_code == HTTPStatus.UNAUTHORIZED
    assert response_get_all_bets_with_cropped_token.json == {
        "ok": False,
        "error_code": HTTPStatus.UNAUTHORIZED,
        "description": "Invalid token, authentication required",
    }


@pytest.fixture()
def setup_app_for_expired_token(app):
    old_jwt_expiration_time = app.config["JWT_EXPIRATION_TIME"]
    app.config["JWT_EXPIRATION_TIME"] = 0

    yield app

    app.config["JWT_EXPIRATION_TIME"] = old_jwt_expiration_time


@pytest.mark.usefixtures("setup_app_for_expired_token")
def test_expired_token(client):
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

    auth_token = response_signup.json["result"]["token"]

    response_current_user = client.get(
        "/api/v1/current_user",
        headers={"Authorization": f"Bearer {auth_token}"},
    )

    assert response_current_user.status_code == HTTPStatus.UNAUTHORIZED
    assert response_current_user.json == {
        "ok": False,
        "error_code": HTTPStatus.UNAUTHORIZED,
        "description": "Expired token, reauthentication required",
    }


def test_invalid_signup_body(client):
    # Try to signup with invalid body
    response_signup = client.post(
        "/api/v1/users/signup",
        json={
            "name": get_random_string(10),
            "first_name": get_random_string(12),
            "last_name": get_random_string(6),
            "passwor": get_random_string(5),
        },
    )

    assert response_signup.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
    assert response_signup.json == {
        "ok": False,
        "error_code": HTTPStatus.UNPROCESSABLE_ENTITY,
        "description": "'password' is a required property",
        "schema": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "first_name": {"type": "string"},
                "last_name": {"type": "string"},
                "password": {"type": "string"},
            },
            "required": ["name", "first_name", "last_name", "password"],
        },
        "path": [],
    }


def test_invalid_login_body(client):
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
    assert response_login.json == {
        "ok": False,
        "error_code": HTTPStatus.UNPROCESSABLE_ENTITY,
        "description": "'name' is a required property",
        "schema": {
            "type": "object",
            "properties": {"name": {"type": "string"}, "password": {"type": "string"}},
            "required": ["name", "password"],
        },
        "path": [],
    }


@pytest.fixture()
def debug_app_for_unexcepted_error_check(app):
    # Unset expiration time configuration. Server will raise an exception.
    old_jwt_expiration_time = app.config["JWT_EXPIRATION_TIME"]
    del app.config["JWT_EXPIRATION_TIME"]

    yield app

    app.config["JWT_EXPIRATION_TIME"] = old_jwt_expiration_time


@pytest.mark.usefixtures("debug_app_for_unexcepted_error_check")
def test_unexpected_error(client):
    # Check unexpected error in debug mode, error should not be obfuscated
    response_signup_debug_unexpected_error = client.post(
        "/api/v1/users/signup",
        json={
            "name": get_random_string(6),
            "first_name": get_random_string(6),
            "last_name": get_random_string(6),
            "password": get_random_string(6),
        },
    )

    assert response_signup_debug_unexpected_error.status_code == HTTPStatus.INTERNAL_SERVER_ERROR
    assert response_signup_debug_unexpected_error.json == {
        "ok": False,
        "error_code": HTTPStatus.INTERNAL_SERVER_ERROR,
        "description": "KeyError: 'JWT_EXPIRATION_TIME'",
    }


@pytest.fixture()
def production_app_unexcepted_error_check(debug_app_for_unexcepted_error_check):
    debug_app_for_unexcepted_error_check.config["DEBUG"] = False

    yield debug_app_for_unexcepted_error_check

    debug_app_for_unexcepted_error_check.config["DEBUG"] = True


@pytest.mark.usefixtures("production_app_unexcepted_error_check")
def test_unexcepted_error(client):
    response_signup_production_unexpected_error = client.post(
        "/api/v1/users/signup",
        json={
            "name": get_random_string(6),
            "first_name": get_random_string(6),
            "last_name": get_random_string(6),
            "password": get_random_string(6),
        },
    )

    assert (
        response_signup_production_unexpected_error.status_code == HTTPStatus.INTERNAL_SERVER_ERROR
    )
    assert response_signup_production_unexpected_error.json == {
        "ok": False,
        "error_code": HTTPStatus.INTERNAL_SERVER_ERROR,
        "description": "Unexcepted error",
    }
