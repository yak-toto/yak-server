import re
import time
from http import HTTPStatus
from typing import TYPE_CHECKING
from uuid import uuid4

from starlette.testclient import TestClient

from testing.util import get_random_string

if TYPE_CHECKING:
    from fastapi import FastAPI


def test_refresh_token_after_signup(app_with_valid_jwt_config: "FastAPI") -> None:
    client = TestClient(app_with_valid_jwt_config)

    response = client.post(
        "/api/v1/users/signup",
        json={
            "name": get_random_string(10),
            "first_name": get_random_string(10),
            "last_name": get_random_string(10),
            "password": get_random_string(150),
        },
    )

    assert response.status_code == HTTPStatus.CREATED

    # Try to refresh the token
    response = client.post("/api/v1/users/refresh")
    assert response.status_code == HTTPStatus.CREATED

    new_access_token = response.json()["result"]["access_token"]

    response = client.get(
        "/api/v1/bets",
        headers={"Authorization": f"Bearer {new_access_token}"},
    )

    assert response.status_code == HTTPStatus.OK


def test_refresh_token_after_login(app_with_valid_jwt_config: "FastAPI") -> None:
    client = TestClient(app_with_valid_jwt_config)

    name = get_random_string(10)
    password = get_random_string(150)

    response = client.post(
        "/api/v1/users/signup",
        json={
            "name": name,
            "first_name": get_random_string(10),
            "last_name": get_random_string(10),
            "password": password,
        },
    )

    assert response.status_code == HTTPStatus.CREATED

    response = client.post(
        "/api/v1/users/login",
        json={
            "name": name,
            "password": password,
        },
    )

    assert response.status_code == HTTPStatus.CREATED

    # Try to refresh the token
    response = client.post("/api/v1/users/refresh")
    assert response.status_code == HTTPStatus.CREATED

    new_access_token = response.json()["result"]["access_token"]

    response = client.get(
        "/api/v1/bets",
        headers={"Authorization": f"Bearer {new_access_token}"},
    )

    assert response.status_code == HTTPStatus.OK


def test_non_existing_refresh_token(app_with_valid_jwt_config: "FastAPI") -> None:
    client = TestClient(app_with_valid_jwt_config)

    response = client.post(
        "/api/v1/users/signup",
        json={
            "name": get_random_string(10),
            "first_name": get_random_string(10),
            "last_name": get_random_string(10),
            "password": get_random_string(150),
        },
    )

    assert response.status_code == HTTPStatus.CREATED

    # Set a non-existing refresh token
    client.cookies.clear()
    client.cookies.set("refresh_token", str(uuid4()))

    # Try to refresh with a non-existing refresh token
    response = client.post("/api/v1/users/refresh")
    assert response.status_code == HTTPStatus.UNAUTHORIZED

    assert response.json() == {
        "ok": False,
        "error_code": HTTPStatus.UNAUTHORIZED,
        "description": "Invalid refresh token",
    }


def test_cookie_header(app_with_valid_jwt_config: "FastAPI") -> None:
    client = TestClient(app_with_valid_jwt_config)

    response = client.post(
        "/api/v1/users/signup",
        json={
            "name": get_random_string(10),
            "first_name": get_random_string(10),
            "last_name": get_random_string(10),
            "password": get_random_string(150),
        },
    )

    assert response.status_code == HTTPStatus.CREATED

    # Check if the Set-Cookie header is present
    assert "set-cookie" in response.headers

    assert re.match(
        r"refresh_token=[a-f0-9]{8}-?[a-f0-9]{4}-?4[a-f0-9]{3}-?[89ab][a-f0-9]{3}-?[a-f0-9]{12}; "
        r"HttpOnly; "
        r"Max-Age=200; "
        r"Path=/; "
        r"SameSite=lax",
        response.headers["set-cookie"],
    )


def test_refresh_token_expired(app_with_null_jwt_refresh_expiration_time: "FastAPI") -> None:
    client = TestClient(app_with_null_jwt_refresh_expiration_time)

    # Login to get the cookie
    response_signup = client.post(
        "/api/v1/users/signup",
        json={
            "name": get_random_string(10),
            "first_name": get_random_string(10),
            "last_name": get_random_string(10),
            "password": get_random_string(150),
        },
    )

    assert response_signup.status_code == HTTPStatus.CREATED

    refresh_cookie = response_signup.cookies["refresh_token"]

    time.sleep(5)  # Wait for the refresh token to expire

    new_client = TestClient(
        app_with_null_jwt_refresh_expiration_time, cookies={"refresh_token": refresh_cookie}
    )

    # Call the refresh endpoint with expired token:
    response = new_client.post("/api/v1/users/refresh")

    assert response.status_code == HTTPStatus.UNAUTHORIZED
    assert response.json() == {
        "ok": False,
        "error_code": HTTPStatus.UNAUTHORIZED,
        "description": "Refresh token expired",
    }


def test_refresh_token_rotation(app_with_valid_jwt_config: "FastAPI") -> None:
    client = TestClient(app_with_valid_jwt_config)

    name = get_random_string(10)
    password = get_random_string(150)

    response = client.post(
        "/api/v1/users/signup",
        json={
            "name": name,
            "first_name": get_random_string(10),
            "last_name": get_random_string(10),
            "password": password,
        },
    )

    assert response.status_code == HTTPStatus.CREATED

    cookies = {"refresh_token": client.cookies["refresh_token"]}

    # Refresh the token
    response = client.post("/api/v1/users/refresh")
    assert response.status_code == HTTPStatus.CREATED

    # Try to refresh the token again with the old refresh token
    new_client = TestClient(app_with_valid_jwt_config, cookies=cookies)

    response = new_client.post("/api/v1/users/refresh")
    assert response.status_code == HTTPStatus.UNAUTHORIZED
    assert response.json() == {
        "ok": False,
        "error_code": HTTPStatus.UNAUTHORIZED,
        "description": "Invalid refresh token",
    }


def test_refresh_token_production_secure(app_with_valid_jwt_config_production: "FastAPI") -> None:
    client = TestClient(app_with_valid_jwt_config_production)

    response = client.post(
        "/api/v1/users/signup",
        json={
            "name": get_random_string(10),
            "first_name": get_random_string(10),
            "last_name": get_random_string(10),
            "password": get_random_string(150),
        },
    )

    assert response.status_code == HTTPStatus.CREATED

    # Check if the refresh token cookie is secure
    assert "set-cookie" in response.headers
    assert re.match(
        r"refresh_token=[a-f0-9]{8}-?[a-f0-9]{4}-?4[a-f0-9]{3}-?[89ab][a-f0-9]{3}-?[a-f0-9]{12}; "
        r"HttpOnly; "
        r"Max-Age=200; "
        r"Path=/; "
        r"SameSite=lax; "
        r"Secure",
        response.headers["set-cookie"],
    )
