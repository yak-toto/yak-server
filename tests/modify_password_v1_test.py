from http import HTTPStatus
from typing import TYPE_CHECKING
from uuid import uuid4

from starlette.testclient import TestClient

from testing.util import get_random_string
from yak_server.cli.admin import create_admin

if TYPE_CHECKING:
    from fastapi import FastAPI
    from sqlalchemy import Engine


def test_modify_password(app_with_valid_jwt_config: "FastAPI", engine_for_test: "Engine") -> None:
    client = TestClient(app_with_valid_jwt_config)

    password = get_random_string(9)
    other_user_name = get_random_string(6)

    # Create admin account
    create_admin(password, engine_for_test)

    response_login_admin = client.post(
        "/api/v1/users/login",
        json={
            "name": "admin",
            "password": password,
        },
    )

    authentication_token = response_login_admin.json()["result"]["access_token"]

    # Create non admin user account
    response_signup_glepape = client.post(
        "/api/v1/users/signup",
        json={
            "name": other_user_name,
            "first_name": "Guillaume",
            "last_name": "Le Pape",
            "password": get_random_string(18),
        },
    )

    user_id = response_signup_glepape.json()["result"]["id"]
    authentication_token_glepape = response_signup_glepape.json()["result"]["access_token"]

    # Check update is properly process
    new_password_other_user = get_random_string(15)

    response_modify_password = client.patch(
        f"/api/v1/users/{user_id}",
        headers={"Authorization": f"Bearer {authentication_token}"},
        json={"password": new_password_other_user},
    )

    assert response_modify_password.status_code == HTTPStatus.OK
    assert response_modify_password.json()["result"]["name"] == other_user_name

    # Check successful login with the new password
    response_login_glepape = client.post(
        "/api/v1/users/login",
        json={"name": other_user_name, "password": new_password_other_user},
    )

    assert response_login_glepape.status_code == HTTPStatus.CREATED
    assert response_login_glepape.json()["result"]["name"] == other_user_name

    # Check glepape user cannot update any password
    response_modify_password_with_glepape_user = client.patch(
        f"/api/v1/users/{user_id}",
        headers={"Authorization": f"Bearer {authentication_token_glepape}"},
        json={"password": "new_new_password"},
    )

    assert response_modify_password_with_glepape_user.status_code == HTTPStatus.UNAUTHORIZED
    assert (
        response_modify_password_with_glepape_user.json()["description"]
        == "Unauthorized access to admin API"
    )

    # Check update is rejected if body does not contain any password
    response_wrong_input = client.patch(
        f"/api/v1/users/{user_id}",
        headers={"Authorization": f"Bearer {authentication_token}"},
        json={"name": other_user_name},
    )

    assert response_wrong_input.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
    assert response_wrong_input.json() == {
        "ok": False,
        "error_code": HTTPStatus.UNPROCESSABLE_ENTITY,
        "description": [
            {"field": "body -> password", "error": "Field required"},
            {"field": "body -> name", "error": "Extra inputs are not permitted"},
        ],
    }

    # Check call is rejected if user_id is invalid
    invalid_user_id = uuid4()

    response_wrong_input = client.patch(
        f"/api/v1/users/{invalid_user_id}",
        headers={"Authorization": f"Bearer {authentication_token}"},
        json={"password": "new_password_for_unknown_user"},
    )

    assert response_wrong_input.status_code == HTTPStatus.NOT_FOUND
    assert response_wrong_input.json()["error_code"] == HTTPStatus.NOT_FOUND
    assert response_wrong_input.json()["description"] == f"User not found: {invalid_user_id}"
