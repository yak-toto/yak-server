from http import HTTPStatus
from typing import TYPE_CHECKING
from uuid import uuid4

from testing.mock import MockSettings
from testing.util import get_random_string
from yak_server.helpers.rules import Rules
from yak_server.helpers.settings import get_settings

if TYPE_CHECKING:
    from fastapi import FastAPI
    from starlette.testclient import TestClient


def test_rule(app: "FastAPI", client: "TestClient") -> None:
    app.dependency_overrides[get_settings] = MockSettings(
        jwt_expiration_time=10,
        jwt_secret_key=get_random_string(100),
        rules=Rules(),
    )

    response_signup = client.post(
        "/api/v1/users/signup",
        json={
            "name": get_random_string(6),
            "first_name": get_random_string(6),
            "last_name": get_random_string(6),
            "password": get_random_string(13),
        },
    )

    assert response_signup.status_code == HTTPStatus.CREATED

    invalid_rule_id = uuid4()

    response_execute_rule = client.post(
        f"/api/v1/rules/{invalid_rule_id}",
        headers={"Authorization": f"Bearer {response_signup.json()['result']['token']}"},
    )

    assert response_execute_rule.status_code == HTTPStatus.NOT_FOUND
    assert response_execute_rule.json() == {
        "ok": False,
        "error_code": HTTPStatus.NOT_FOUND,
        "description": f"Rule not found: {invalid_rule_id}",
    }
