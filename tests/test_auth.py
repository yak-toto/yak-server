from unittest.mock import ANY

from .constants import HttpCode
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
    assert response_signup.status_code == HttpCode.CREATED
    assert response_signup.json == {
        "ok": True,
        "result": {"id": ANY, "name": user_name, "token": ANY},
    }

    # login test
    response_login = client.post(
        "/api/v1/users/login",
        json={"name": user_name, "password": password},
    )
    assert response_login.status_code == HttpCode.CREATED
    assert response_login.json == {
        "ok": True,
        "result": {"id": ANY, "name": user_name, "token": ANY},
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
    assert response_signup.status_code == HttpCode.CREATED
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
    assert response_second_signup.status_code == HttpCode.UNAUTHORIZED
    assert response_second_signup.json == {
        "ok": False,
        "error_code": HttpCode.UNAUTHORIZED,
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

    assert response_login.status_code == HttpCode.UNAUTHORIZED
    assert response_login.json == {
        "ok": False,
        "error_code": HttpCode.UNAUTHORIZED,
        "description": "Invalid credentials",
    }
