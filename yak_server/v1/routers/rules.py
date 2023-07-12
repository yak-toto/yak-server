from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import APIRouter, Depends

from yak_server.config_file import Settings, get_settings
from yak_server.helpers.rules import RULE_MAPPING
from yak_server.v1.helpers.auth import get_current_user
from yak_server.v1.helpers.database import get_db
from yak_server.v1.helpers.errors import RuleNotFound
from yak_server.v1.models.generic import GenericOut

if TYPE_CHECKING:
    from pydantic import UUID4
    from sqlalchemy.orm import Session

    from yak_server.database.models import UserModel

router = APIRouter(prefix="/rules", tags=["rules"])


@router.post("/{rule_id}")
def execute_rule(
    rule_id: UUID4,
    db: Session = Depends(get_db),
    user: UserModel = Depends(get_current_user),
    settings: Settings = Depends(get_settings),
) -> GenericOut[str]:
    found_rule = None

    for rule in settings.rules:
        if rule.id == rule_id:
            found_rule = rule
            break

    if found_rule is None:
        raise RuleNotFound(rule_id)

    rule_config = found_rule.config
    rule_function = RULE_MAPPING[found_rule.id]

    rule_function(db, user, rule_config)

    return GenericOut(result="")
