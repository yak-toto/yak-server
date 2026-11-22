from fastapi import APIRouter, status
from sqlalchemy import text

from .helpers.database import SessionDep
from .v1.models.generic import ErrorOut, GenericOut

router = APIRouter(prefix="/health", tags=["health"])


@router.get(
    "",
    responses={status.HTTP_503_SERVICE_UNAVAILABLE: {"model": ErrorOut}},
    response_model_exclude_none=True,
)
def health_check(db: SessionDep) -> GenericOut[None]:
    db.execute(text("SELECT 1"))

    return GenericOut(ok=True, result=None)
