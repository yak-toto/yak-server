from fastapi import APIRouter, Depends
from pydantic import UUID4
from sqlalchemy.orm import Session

from yak_server.config_file import Settings, get_settings
from yak_server.database.models import UserModel
from yak_server.v1.helpers.auth import get_current_user
from yak_server.v1.helpers.database import get_db
from yak_server.v1.helpers.errors import RuleNotFound
from yak_server.v1.models.generic import GenericOut

router = APIRouter(prefix="/rules", tags=["rules"])


@router.post("/{rule_id}")
def execute_rule(
    rule_id: UUID4,
    db: Session = Depends(get_db),
    user: UserModel = Depends(get_current_user),
    settings: Settings = Depends(get_settings),
) -> GenericOut[None]:
    rule_id = str(rule_id)

    if rule_id not in settings.rules:
        raise RuleNotFound(rule_id)

    rule_config = settings.rules[rule_id].config
    rule_function = settings.rules[rule_id].function

    rule_function(db, user, rule_config)

    return GenericOut(result=None)
