from http import HTTPStatus
from typing import TYPE_CHECKING

from sqlalchemy import TextClause
from sqlalchemy.exc import SQLAlchemyError
from starlette.testclient import TestClient

from yak_server.helpers.database import get_db

if TYPE_CHECKING:
    from fastapi import FastAPI


def test_health_check_ok(app_with_valid_jwt_config: "FastAPI") -> None:
    client = TestClient(app_with_valid_jwt_config)

    response = client.get("/api/health/")

    assert response.status_code == HTTPStatus.OK
    assert response.json() == {"ok": True}


class FakeDbSession:
    def execute(self, statement: TextClause) -> None:  # noqa: PLR6301
        raise SQLAlchemyError(statement)


def test_health_check_ko(app_with_valid_jwt_config: "FastAPI") -> None:
    client = TestClient(app_with_valid_jwt_config)

    app_with_valid_jwt_config.dependency_overrides[get_db] = FakeDbSession

    response = client.get("/api/health/")

    assert response.status_code == HTTPStatus.SERVICE_UNAVAILABLE
    assert response.json() == {"ok": False, "error_code": 503, "description": "Service Unavailable"}
