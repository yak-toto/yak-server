import hashlib
import json
from copy import deepcopy
from typing import Any

from fastapi import APIRouter, FastAPI, status
from fastapi.requests import Request

from yak_server.v1.models.generic import GenericOut, ValidationErrorOut
from yak_server.v1.models.version import VersionOut

router = APIRouter(prefix="/version", tags=["version"])


def hash_json(obj: dict[str, Any]) -> str:
    canonical = json.dumps(obj, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode()).hexdigest()


def extract_metadata(app: "FastAPI") -> tuple[str, str]:
    schema = deepcopy(app.openapi())

    version = schema["info"].pop("version")

    return version, hash_json(schema)


@router.get("", responses={status.HTTP_422_UNPROCESSABLE_CONTENT: {"model": ValidationErrorOut}})
def get_version(request: Request) -> GenericOut[VersionOut]:
    version, schema_hash = extract_metadata(request.app)

    return GenericOut[VersionOut](result=VersionOut(version=version, schema_hash=schema_hash))
