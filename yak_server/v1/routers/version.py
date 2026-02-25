from importlib.metadata import version

from fastapi import APIRouter, status

from yak_server.v1.models.generic import GenericOut, ValidationErrorOut
from yak_server.v1.models.version import VersionOut

router = APIRouter(prefix="/version", tags=["version"])


@router.get("", responses={status.HTTP_422_UNPROCESSABLE_CONTENT: {"model": ValidationErrorOut}})
def get_version() -> GenericOut[VersionOut]:
    return GenericOut[VersionOut](result=VersionOut(version=version("yak-server")))
