import secrets
import string
from http import HTTPStatus
from typing import TYPE_CHECKING

import pytest
from starlette.testclient import TestClient

from yak_server.helpers.password_validator import (
    NoDigitError,
    NoLowerCaseError,
    NoUpperCaseError,
    SpaceError,
    TooShortError,
    validate_password,
)

from .utils import get_random_string

if TYPE_CHECKING:
    from fastapi import FastAPI


def test_valid_password() -> None:
    assert validate_password(get_random_string(18)) is None


def test_password_too_short() -> None:
    with pytest.raises(TooShortError) as exception:
        validate_password(get_random_string(6))

    assert str(exception.value) == "Password is too short. Minimum size is 8."


def test_password_without_upper_case_letter() -> None:
    with pytest.raises(NoUpperCaseError) as exception:
        validate_password(
            secrets.choice(string.ascii_lowercase)
            + secrets.choice(string.digits)
            + "".join(secrets.choice(string.ascii_lowercase + string.digits) for _ in range(10))
        )

    assert str(exception.value) == "At least one upper-case letter expected."


def test_password_without_lower_case_letter() -> None:
    with pytest.raises(NoLowerCaseError) as exception:
        validate_password(
            secrets.choice(string.ascii_uppercase)
            + secrets.choice(string.digits)
            + "".join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(10))
        )

    assert str(exception.value) == "At least one lower-case letter expected."


def test_password_without_digits() -> None:
    with pytest.raises(NoDigitError) as exception:
        validate_password(
            secrets.choice(string.ascii_uppercase)
            + secrets.choice(string.ascii_lowercase)
            + "".join(secrets.choice(string.ascii_letters) for _ in range(10))
        )

    assert str(exception.value) == "At least one digit expected."


def test_password_with_spaces() -> None:
    with pytest.raises(SpaceError) as exception:
        validate_password(
            secrets.choice(string.ascii_uppercase)
            + secrets.choice(string.ascii_lowercase)
            + secrets.choice(string.digits)
            + "".join(secrets.choice(string.ascii_letters + string.digits) for _ in range(10))
            + " " * 10
        )

    assert str(exception.value) == "Password must not contain spaces."


def test_password_requirements_v1(app_with_valid_jwt_config: "FastAPI") -> None:
    client = TestClient(app_with_valid_jwt_config)

    response = client.get("/api/v1/users/signup/password_requirements")

    assert response.status_code == HTTPStatus.OK
    assert response.json() == {
        "ok": True,
        "result": {
            "minimum_length": 8,
            "uppercase": True,
            "lowercase": True,
            "digit": True,
            "no_space": True,
        },
    }


def test_password_requirements_v2(app_with_valid_jwt_config: "FastAPI") -> None:
    client = TestClient(app_with_valid_jwt_config)

    query = """
        query {
            passwordRequirements {
                minimumLength
                uppercase
                lowercase
                digit
                noSpace
            }
        }
    """

    response = client.post("/api/v2", json={"query": query})

    assert response.status_code == HTTPStatus.OK
    assert response.json() == {
        "data": {
            "passwordRequirements": {
                "minimumLength": 8,
                "uppercase": True,
                "lowercase": True,
                "digit": True,
                "noSpace": True,
            }
        }
    }
