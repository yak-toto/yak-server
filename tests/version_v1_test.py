from http import HTTPStatus
from importlib.metadata import version
from typing import TYPE_CHECKING

from starlette.testclient import TestClient

if TYPE_CHECKING:
    from fastapi import FastAPI


def test_get_version(app_with_valid_jwt_config: "FastAPI") -> None:
    client = TestClient(app_with_valid_jwt_config)

    response = client.get("/api/version")

    assert response.status_code == HTTPStatus.OK
    assert response.json() == {"ok": True, "result": {"version": version("yak-server")}}
