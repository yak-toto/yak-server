from typing import Annotated

from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
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
    try:
        db.execute(text("SELECT 1"))
    except SQLAlchemyError:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "ok": False,
                "error_code": status.HTTP_503_SERVICE_UNAVAILABLE,
                "description": "Service Unavailable",
            },
        )
    else:
        return GenericOut(ok=True, result=None)
