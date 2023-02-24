from http import HTTPStatus
from uuid import uuid4

from .test_utils import get_random_string


def test_modify_password(client):
    admin_name = "admin"
    other_user_name = get_random_string(6)

    # Create admin account
    response_signup_admin = client.post(
        "/api/v1/users/signup",
        json={
            "name": admin_name,
            "first_name": "admin",
            "last_name": "admin",
            "password": "admin",
        },
    )

    authentification_token = response_signup_admin.json["result"]["token"]

    # Create non admin user account
    response_signup_glepape = client.post(
        "/api/v1/users/signup",
        json={
            "name": other_user_name,
            "first_name": "Guillaume",
            "last_name": "Le Pape",
            "password": "password",
        },
    )

    user_id = response_signup_glepape.json["result"]["id"]
    authentification_token_glepape = response_signup_glepape.json["result"]["token"]

    # Check update is properly process
    new_password_other_user = "new_password"

    response_modify_password = client.patch(
        f"/api/v1/users/{user_id}",
        headers={"Authorization": f"Bearer {authentification_token}"},
        json={"password": new_password_other_user},
    )

    assert response_modify_password.status_code == HTTPStatus.OK
    assert response_modify_password.json["result"]["name"] == other_user_name

    # Check login succesful with the new password
    response_login_glepape = client.post(
        "/api/v1/users/login",
        json={"name": other_user_name, "password": new_password_other_user},
    )

    assert response_login_glepape.status_code == HTTPStatus.CREATED
    assert response_login_glepape.json["result"]["name"] == other_user_name

    # Check glepape user cannot update any password
    response_modify_password_with_glepape_user = client.patch(
        f"/api/v1/users/{user_id}",
        headers={"Authorization": f"Bearer {authentification_token_glepape}"},
        json={"password": "new_new_password"},
    )

    assert response_modify_password_with_glepape_user.status_code == HTTPStatus.UNAUTHORIZED
    assert (
        response_modify_password_with_glepape_user.json["description"]
        == "Unauthorized access to admin API"
    )

    # Check update is rejected if body does not contain any password
    response_wrong_input = client.patch(
        f"/api/v1/users/{user_id}",
        headers={"Authorization": f"Bearer {authentification_token}"},
        json={"name": other_user_name},
    )

    assert response_wrong_input.status_code == HTTPStatus.UNAUTHORIZED
    assert response_wrong_input.json["description"] == "Wrong inputs"

    # Check call is rejected if user_id is invalid
    response_wrong_input = client.patch(
        f"/api/v1/users/{uuid4()}",
        headers={"Authorization": f"Bearer {authentification_token}"},
        json={"password": "new_password_for_unknown_user"},
    )

    assert response_wrong_input.status_code == HTTPStatus.NOT_FOUND
    assert response_wrong_input.json["error_code"] == HTTPStatus.NOT_FOUND
    assert response_wrong_input.json["description"] == "User not found"
