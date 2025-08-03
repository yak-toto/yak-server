import time
from http import HTTPStatus
from typing import TYPE_CHECKING

from starlette.testclient import TestClient

from testing.util import get_random_string

if TYPE_CHECKING:
    from fastapi import FastAPI


def test_refresh_after_signup(app_with_valid_jwt_config: "FastAPI") -> None:
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

    refresh_token = response.json()["result"]["refresh_token"]

    # Try to refresh the token
    response = client.post("/api/v1/users/refresh", json={"refresh_token": refresh_token})
    assert response.status_code == HTTPStatus.CREATED

    new_access_token = response.json()["result"]["access_token"]

    response = client.get(
        "/api/v1/bets",
        headers={"Authorization": f"Bearer {new_access_token}"},
    )

    assert response.status_code == HTTPStatus.OK


def test_refresh_after_login(app_with_valid_jwt_config: "FastAPI") -> None:
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

    refresh_token = response.json()["result"]["refresh_token"]

    response = client.post(
        "/api/v1/users/login",
        json={
            "name": name,
            "password": password,
        },
    )

    assert response.status_code == HTTPStatus.CREATED

    # Try to refresh the token
    response = client.post("/api/v1/users/refresh", json={"refresh_token": refresh_token})
    assert response.status_code == HTTPStatus.CREATED

    new_access_token = response.json()["result"]["access_token"]

    response = client.get(
        "/api/v1/bets",
        headers={"Authorization": f"Bearer {new_access_token}"},
    )

    assert response.status_code == HTTPStatus.OK


def test_refresh_token_expired(app_with_null_jwt_refresh_expiration_time: "FastAPI") -> None:
    client = TestClient(app_with_null_jwt_refresh_expiration_time)

    # Login to get the refresh token
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

    refresh_token = response_signup.json()["result"]["refresh_token"]

    time.sleep(5)  # Wait for the refresh token to expire

    # Call the refresh endpoint with expired token:
    response = client.post("/api/v1/users/refresh", json={"refresh_token": refresh_token})

    assert response.status_code == HTTPStatus.UNAUTHORIZED
    assert response.json() == {
        "ok": False,
        "error_code": HTTPStatus.UNAUTHORIZED,
        "description": "Expired access token, re-authentication required",
    }


def test_refresh_token_cannot_access_protected_resources(
    app_with_valid_jwt_config: "FastAPI",
) -> None:
    """Test that refresh tokens cannot be used to access protected endpoints."""
    client = TestClient(app_with_valid_jwt_config)

    # Signup to get both tokens
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

    refresh_token = response.json()["result"]["refresh_token"]
    access_token = response.json()["result"]["access_token"]

    # Verify access token works for protected resources
    response_with_access_token = client.get(
        "/api/v1/bets",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response_with_access_token.status_code == HTTPStatus.OK

    # Try to access protected resource with refresh token - should fail
    response_with_refresh_token = client.get(
        "/api/v1/bets",
        headers={"Authorization": f"Bearer {refresh_token}"},
    )
    assert response_with_refresh_token.status_code == HTTPStatus.UNAUTHORIZED
    assert response_with_refresh_token.json() == {
        "ok": False,
        "error_code": HTTPStatus.UNAUTHORIZED,
        "description": "Invalid access token, authentication required",
    }

    # Test with another protected endpoint to ensure consistency
    response_current_user_with_refresh = client.get(
        "/api/v1/users/current",
        headers={"Authorization": f"Bearer {refresh_token}"},
    )
    assert response_current_user_with_refresh.status_code == HTTPStatus.UNAUTHORIZED
    assert response_current_user_with_refresh.json() == {
        "ok": False,
        "error_code": HTTPStatus.UNAUTHORIZED,
        "description": "Invalid access token, authentication required",
    }
