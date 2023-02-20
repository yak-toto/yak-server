from random import randint
from uuid import uuid4

from .constants import HttpCode
from .test_utils import get_random_string


def test_admin_api_users(client):
    # Signup admin account
    admin_user = {
        "name": "admin",
        "first_name": get_random_string(6),
        "last_name": get_random_string(4),
        "password": get_random_string(10),
    }

    response_admin_signup = client.post(
        "/api/v1/users/signup",
        json=admin_user,
    )

    admin_user["id"] = response_admin_signup.json["result"]["id"]
    admin_user["token"] = response_admin_signup.json["result"]["token"]

    # Signup 10 random others accounts
    users = [
        {
            "name": get_random_string(randint(6, 12)),
            "first_name": get_random_string(10),
            "last_name": get_random_string(10),
            "password": get_random_string(randint(2, 12)),
        }
        for _ in range(10)
    ]

    for user in users:
        response_user_signup = client.post("/api/v1/users/signup", json=user)
        user["id"] = response_user_signup.json["result"]["id"]
        user["token"] = response_user_signup.json["result"]["token"]

    response_get_all_users = client.get(
        "/api/v1/users",
        headers={"Authorization": f"Bearer {admin_user['token']}"},
    )

    assert response_get_all_users.status_code == HttpCode.OK
    assert sorted([user["name"] for user in response_get_all_users.json["result"]]) == sorted(
        [user["name"] for user in [*users, admin_user]],
    )

    # Try to GET /users using a non admin account
    response_all_get_users_other_user = client.get(
        "/api/v1/users",
        headers={"Authorization": f"Bearer {users[0]['token']}"},
    )

    assert response_all_get_users_other_user.status_code == HttpCode.UNAUTHORIZED
    assert (
        response_all_get_users_other_user.json["description"] == "Unauthorized access to admin API"
    )

    # Check GET /users/{userId} using admin account
    response_get_one_user_success = client.get(
        f"/api/v1/users/{users[5]['id']}",
        headers={"Authorization": f"Bearer {admin_user['token']}"},
    )

    assert response_get_one_user_success.status_code == HttpCode.OK
    assert response_get_one_user_success.json["result"] == {
        "id": users[5]["id"],
        "name": users[5]["name"],
    }

    # Check GET /users/{userId} error if user id does not exist
    response_get_one_user_invalid_id = client.get(
        f"/api/v1/users/{uuid4()}",
        headers={"Authorization": f"Bearer {admin_user['token']}"},
    )

    assert response_get_one_user_invalid_id.status_code == HttpCode.NOT_FOUND
    assert response_get_one_user_invalid_id.json == {
        "ok": False,
        "error_code": HttpCode.NOT_FOUND,
        "description": "User not found",
    }

    # Check GET /users/{userId} is unauthorized to others users than admin
    response_get_one_user_unauthorized = client.get(
        f"/api/v1/users/{users[2]['id']}",
        headers={"Authorization": f"Bearer {users[3]['token']}"},
    )

    assert response_get_one_user_unauthorized.status_code == HttpCode.UNAUTHORIZED
    assert response_get_one_user_unauthorized.json == {
        "ok": False,
        "error_code": HttpCode.UNAUTHORIZED,
        "description": "Unauthorized access to admin API",
    }
