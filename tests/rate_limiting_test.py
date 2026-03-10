from http import HTTPStatus
from typing import TYPE_CHECKING

from fastapi import FastAPI
from fastapi.testclient import TestClient

from testing.util import get_random_string

if TYPE_CHECKING:
    from fastapi import FastAPI


def test_rate_limiter_signup_login(app_with_rate_limiter: "FastAPI") -> None:
    client = TestClient(app_with_rate_limiter)

    login_request_bodies = [
        {"name": get_random_string(10), "password": get_random_string(150)} for _ in range(5)
    ]
    signup_request_bodies = [
        {**login_request, "first_name": get_random_string(10), "last_name": get_random_string(10)}
        for login_request in login_request_bodies
    ]

    # Make 6 signup request, 6th should return 429 TOO MANY REQUEST
    for signup_request in signup_request_bodies:
        response_signup = client.post("/api/v1/users/signup", json=signup_request)

        assert response_signup.status_code == HTTPStatus.CREATED

    response_signup = client.post(
        "/api/v1/users/signup",
        json={
            "name": get_random_string(10),
            "first_name": get_random_string(10),
            "last_name": get_random_string(10),
            "password": get_random_string(150),
        },
    )

    assert response_signup.status_code == HTTPStatus.TOO_MANY_REQUESTS
    assert response_signup.json() == {
        "ok": False,
        "error_code": HTTPStatus.TOO_MANY_REQUESTS,
        "description": "Rate limit exceeded. Please try again later.",
    }

    # Make 6 login request, 6th should return 429 TOO MANY REQUEST
    for login_request in login_request_bodies:
        response_login = client.post("/api/v1/users/login", json=login_request)

        assert response_login.status_code == HTTPStatus.CREATED

    response_login = client.post(
        "/api/v1/users/login",
        json={
            "name": get_random_string(10),
            "password": get_random_string(150),
        },
    )

    assert response_login.status_code == HTTPStatus.TOO_MANY_REQUESTS
    assert response_login.json() == {
        "ok": False,
        "error_code": HTTPStatus.TOO_MANY_REQUESTS,
        "description": "Rate limit exceeded. Please try again later.",
    }


def test_rate_limiter_global(app_with_rate_limiter: "FastAPI") -> None:
    client = TestClient(app_with_rate_limiter)

    for _ in range(200):
        response = client.get("/api/health")

        assert response.status_code == HTTPStatus.OK

    response = client.get("/api/health")

    assert response.status_code == HTTPStatus.TOO_MANY_REQUESTS
    assert response.json() == {
        "ok": False,
        "error_code": HTTPStatus.TOO_MANY_REQUESTS,
        "description": "Rate limit exceeded. Please try again later.",
    }
