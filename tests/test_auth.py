from unittest.mock import ANY

from .constants import HttpCode


def test_valid_auth(client):
    # signup test
    response_signup = client.post(
        "/api/v1/users/signup",
        json={
            "name": "admin",
            "first_name": "admin",
            "last_name": "admin",
            "password": "admin",
        },
    )
    assert response_signup.status_code == HttpCode.CREATED
    assert response_signup.json == {
        "ok": True,
        "result": {"id": ANY, "name": "admin", "token": ANY},
    }

    # login test
    response_login = client.post(
        "/api/v1/users/login",
        json={"name": "admin", "password": "admin"},
    )
    assert response_login.status_code == HttpCode.CREATED
    assert response_login.json == {
        "ok": True,
        "result": {"id": ANY, "name": "admin", "token": ANY},
    }

    auth_token = response_login.json["result"]["token"]

    # current user tests
    response_current_user = client.get(
        "/api/v1/current_user",
        headers=[("Authorization", f"Bearer {auth_token}")],
    )
    assert response_current_user.status_code == HttpCode.OK
    assert response_current_user.json == {
        "ok": True,
        "result": {"id": ANY, "name": "admin"},
    }


def test_double_signup(client):
    # signup test
    response_signup = client.post(
        "/api/v1/users/signup",
        json={
            "name": "user2",
            "first_name": "admin",
            "last_name": "admin",
            "password": "admin",
        },
    )
    assert response_signup.status_code == HttpCode.CREATED
    assert response_signup.json == {
        "ok": True,
        "result": {"id": ANY, "name": "user2", "token": ANY},
    }

    # signup with same name test
    response_second_signup = client.post(
        "/api/v1/users/signup",
        json={
            "name": "user2",
            "first_name": "admin",
            "last_name": "admin",
            "password": "admin",
        },
    )
    assert response_second_signup.status_code == HttpCode.UNAUTHORIZED
    assert response_second_signup.json == {
        "ok": False,
        "error_code": HttpCode.UNAUTHORIZED,
        "description": "Name already exists: user2",
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

    assert response_login.status_code == HttpCode.UNAUTHORIZED
    assert response_login.json == {
        "ok": False,
        "error_code": HttpCode.UNAUTHORIZED,
        "description": "Invalid credentials",
    }
