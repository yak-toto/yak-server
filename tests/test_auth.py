from http import HTTPStatus
from time import sleep
from unittest.mock import ANY

from .test_utils import get_random_string


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
    client.post(
        "/api/v1/users/signup",
        json={
            "name": "glepape",
            "first_name": "Guillaume",
            "last_name": "Le Pape",
            "password": "admin",
        },
    )

    response_login = client.post(
        "/api/v1/users/login",
        json={"name": "glepape", "password": "wrong_password"},
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
        "description": "Invalid token. Registration and / or authentication required",
    }

    response_get_all_bets_with_cropped_token = client.get(
        "/api/v1/bets",
        headers={"Authorization": f"Bearer {auth_token[:17]}{auth_token[12:]}"},
    )

    assert response_get_all_bets_with_cropped_token.status_code == HTTPStatus.UNAUTHORIZED
    assert response_get_all_bets_with_cropped_token.json == {
        "ok": False,
        "error_code": HTTPStatus.UNAUTHORIZED,
        "description": "Invalid token. Registration and / or authentication required",
    }


def test_expired_token(client, app):
    old_jwt_expiration_time = app.config["JWT_EXPIRATION_TIME"]
    app.config["JWT_EXPIRATION_TIME"] = 1

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

    sleep(1)

    response_current_user = client.get(
        "/api/v1/current_user",
        headers={"Authorization": f"Bearer {auth_token}"},
    )

    assert response_current_user.status_code == HTTPStatus.UNAUTHORIZED
    assert response_current_user.json == {
        "ok": False,
        "error_code": HTTPStatus.UNAUTHORIZED,
        "description": "Expired token. Reauthentication required.",
    }

    app.config["JWT_EXPIRATION_TIME"] = old_jwt_expiration_time


def test_invalid_signup_body(client, app):
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

    assert response_signup.status_code == HTTPStatus.UNAUTHORIZED
    assert response_signup.json == {
        "ok": False,
        "error_code": HTTPStatus.UNAUTHORIZED,
        "description": "Wrong inputs",
    }


def test_invalid_login_body(client, app):
    user_name = get_random_string(6)
    password = get_random_string(10)

    response_signup = client.post(
        "/api/v1/users/signup",
        json={
            "name": get_random_string(10),
            "first_name": get_random_string(12),
            "last_name": get_random_string(6),
            "passwor": get_random_string(5),
        },
    )

    assert response_signup.status_code == HTTPStatus.UNAUTHORIZED

    response_login = client.post(
        "/api/v1/users/login",
        json={
            "nme": user_name,
            "password": password,
        },
    )

    assert response_login.status_code == HTTPStatus.UNAUTHORIZED
    assert response_login.json == {"description": "Wrong inputs", "error_code": 401, "ok": False}
