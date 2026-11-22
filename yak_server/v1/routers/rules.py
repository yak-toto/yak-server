from fastapi import APIRouter, status
from pydantic import UUID4

from yak_server.database.models import Role
from yak_server.helpers.database import SessionDep
from yak_server.helpers.rules import RULE_MAPPING, Rules
from yak_server.helpers.settings import RulesDep
from yak_server.v1.helpers.auth import CurrentUserDep
from yak_server.v1.helpers.errors import RuleNotFound, UnauthorizedAccessToAdminAPI
from yak_server.v1.helpers.responses import error_responses
from yak_server.v1.models.generic import GenericOut

router = APIRouter(
    prefix="/rules",
    tags=["rules"],
    responses=error_responses(status.HTTP_401_UNAUTHORIZED),
)


@router.post("/{rule_id}", responses=error_responses(status.HTTP_404_NOT_FOUND))
def execute_rule(
    rule_id: UUID4,
    db: SessionDep,
    user: CurrentUserDep,
    rules: RulesDep,
) -> GenericOut[str]:
    rule_metadata = RULE_MAPPING.get(rule_id)

    if rule_metadata is None:
        raise RuleNotFound(rule_id)

    if rule_metadata.required_admin is True and user.role != Role.ADMIN:
        raise UnauthorizedAccessToAdminAPI

    rule_metadata.function(db, user, getattr(rules, rule_metadata.attribute))

    return GenericOut(result="")


@router.get("")
def retrieve_rules_configuration(_: CurrentUserDep, rules: RulesDep) -> GenericOut[Rules]:
    return GenericOut(result=rules)
