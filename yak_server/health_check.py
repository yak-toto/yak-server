from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from .helpers.database import get_db
from .v1.models.generic import ErrorOut, GenericOut

router = APIRouter(prefix="/health", tags=["health"])


@router.get(
    "/",
    responses={status.HTTP_503_SERVICE_UNAVAILABLE: {"model": ErrorOut}},
    response_model_exclude_none=True,
)
def health_check(db: Annotated[Session, Depends(get_db)]) -> GenericOut[None]:
    db.execute(text("SELECT 1"))

    return GenericOut(ok=True, result=None)
