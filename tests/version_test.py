from http import HTTPStatus
from typing import TYPE_CHECKING

from starlette.testclient import TestClient

from yak_server import __version__

if TYPE_CHECKING:
    from fastapi import FastAPI


def test_version(
    app_with_valid_jwt_config: "FastAPI",
) -> None:
    client = TestClient(app_with_valid_jwt_config)

    response = client.get("/api/version")
    assert response.status_code == HTTPStatus.OK
    assert response.json() == {"version": __version__}
