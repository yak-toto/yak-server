from unittest.mock import Mock


def test_valid_auth(client, monkeypatch):
    # signup test
    monkeypatch.setattr(
        "uuid.uuid4", Mock(return_value="b31d9d4f-22f5-4122-85dd-48089d42fd0a")
    )

    response_signup = client.post(
        "/api/v1/signup",
        json={
            "name": "admin",
            "first_name": "admin",
            "last_name": "admin",
            "password": "admin",
        },
    )
    assert response_signup.status_code == 201
    assert response_signup.json["ok"]
    assert (
        response_signup.json["result"]["id"] == "b31d9d4f-22f5-4122-85dd-48089d42fd0a"
    )
    assert response_signup.json["result"]["name"] == "admin"

    monkeypatch.delattr("uuid.uuid4")

    # login test
    response_login = client.post(
        "/api/v1/login", json={"name": "admin", "password": "admin"}
    )
    response_login_body = response_login.json
    auth_token = response_login_body["result"].pop("token")
    assert response_login.status_code == 201
    assert response_login_body == {
        "ok": True,
        "result": {"id": "b31d9d4f-22f5-4122-85dd-48089d42fd0a", "name": "admin"},
    }

    # current user tests
    response_current_user = client.get(
        "api/v1/current_user", headers=[("Authorization", f"Bearer: {auth_token}")]
    )
    assert response_current_user.status_code == 200
    assert response_current_user.json == {
        "ok": True,
        "result": {"id": "b31d9d4f-22f5-4122-85dd-48089d42fd0a", "name": "admin"},
    }


def test_double_signup(client, monkeypatch):
    # signup test
    monkeypatch.setattr(
        "uuid.uuid4", Mock(return_value="a9e14635-8983-45ab-8afa-eb920866c60e")
    )

    response_signup = client.post(
        "/api/v1/signup",
        json={
            "name": "user2",
            "first_name": "admin",
            "last_name": "admin",
            "password": "admin",
        },
    )
    assert response_signup.status_code == 201
    assert response_signup.json["ok"]
    assert (
        response_signup.json["result"]["id"] == "a9e14635-8983-45ab-8afa-eb920866c60e"
    )
    assert response_signup.json["result"]["name"] == "user2"

    monkeypatch.delattr("uuid.uuid4")

    # signup with same name test
    response_second_signup = client.post(
        "/api/v1/signup",
        json={
            "name": "user2",
            "first_name": "admin",
            "last_name": "admin",
            "password": "admin",
        },
    )
    assert response_second_signup.status_code == 401
    assert response_second_signup.json == {
        "ok": False,
        "error_code": 401,
        "description": "Name already exists: user2",
    }


def test_login_wrong_password(client):
    client.post(
        "api/v1/signup",
        json={
            "name": "glepape",
            "first_name": "Guillaume",
            "last_name": "Le Pape",
            "password": "admin",
        },
    )

    response_login = client.post(
        "api/v1/login", json={"name": "glepape", "password": "wrong_password"}
    )

    assert response_login.status_code == 401
    assert response_login.json == {
        "ok": False,
        "error_code": 401,
        "description": "Invalid credentials",
    }
