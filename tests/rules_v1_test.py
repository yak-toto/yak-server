from http import HTTPStatus
from typing import TYPE_CHECKING
from uuid import uuid4

from starlette.testclient import TestClient

from testing.util import get_random_string, get_resources_path
from yak_server.cli.admin import create_admin
from yak_server.cli.database import initialize_database
from yak_server.helpers.rules import Rules

if TYPE_CHECKING:
    from fastapi import FastAPI
    from sqlalchemy import Engine


def test_rule(app_with_valid_jwt_config: "FastAPI") -> None:
    client = TestClient(app_with_valid_jwt_config)

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
        headers={"Authorization": f"Bearer {response_signup.json()['result']['access_token']}"},
    )

    assert response_execute_rule.status_code == HTTPStatus.NOT_FOUND
    assert response_execute_rule.json() == {
        "ok": False,
        "error_code": "rule_not_found",
        "description": f"Rule not found: {invalid_rule_id}",
    }


def test_retrieve_rules(
    app_and_rules_for_compute_points: tuple["FastAPI", Rules],
    engine_for_test: "Engine",
) -> None:
    app, rules = app_and_rules_for_compute_points

    client = TestClient(app)

    initialize_database(engine_for_test, get_resources_path("test_compute_points_v1"))

    # Signup admin
    password = get_random_string(15)

    create_admin(password, engine_for_test)

    response_login_admin = client.post(
        "/api/v1/users/login",
        json={
            "name": "admin",
            "password": password,
        },
    )

    assert response_login_admin.status_code == HTTPStatus.CREATED

    response_retrieve_rules = client.get("/api/v1/rules")

    assert response_retrieve_rules.json() == {"ok": True, "result": rules.model_dump()}
