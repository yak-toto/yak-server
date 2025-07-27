from typing import Annotated

from fastapi import APIRouter, Depends, status
from pydantic import UUID4
from sqlmodel import Session

from yak_server.database.models import UserModel
from yak_server.helpers.database import get_db
from yak_server.helpers.rules import RULE_MAPPING
from yak_server.helpers.settings import Settings, get_settings
from yak_server.v1.helpers.auth import get_current_user
from yak_server.v1.helpers.errors import RuleNotFound, UnauthorizedAccessToAdminAPI
from yak_server.v1.models.generic import ErrorOut, GenericOut, ValidationErrorOut

router = APIRouter(prefix="/rules", tags=["rules"])


@router.post(
    "/{rule_id}",
    responses={
        status.HTTP_401_UNAUTHORIZED: {"model": ErrorOut},
        status.HTTP_404_NOT_FOUND: {"model": ErrorOut},
        status.HTTP_422_UNPROCESSABLE_ENTITY: {"model": ValidationErrorOut},
    },
)
def execute_rule(
    rule_id: UUID4,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[UserModel, Depends(get_current_user)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> GenericOut[str]:
    rule_metadata = RULE_MAPPING.get(rule_id)

    if rule_metadata is None:
        raise RuleNotFound(rule_id)

    if rule_metadata.required_admin is True and user.name != "admin":
        raise UnauthorizedAccessToAdminAPI

    rule_metadata.function(db, user, getattr(settings.rules, rule_metadata.attribute))

    return GenericOut(result="")
