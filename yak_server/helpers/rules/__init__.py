from typing import Callable, Optional
from uuid import UUID

from pydantic import BaseModel
from sqlalchemy.orm import Session

from yak_server.database.models import UserModel

from .compute_final_from_rank import (
    RuleComputeFinaleFromGroupRank,
    compute_finale_phase_from_group_rank,
)


class Rules(BaseModel):
    compute_finale_phase_from_group_rank: Optional[RuleComputeFinaleFromGroupRank] = None


class RuleMetadata:
    def __init__(
        self,
        *,
        function: Callable[
            [Session, UserModel, RuleComputeFinaleFromGroupRank],
            None,
        ],
        attribute: str,
        required_admin: bool = False,
    ) -> None:
        self.function = function
        self.attribute = attribute
        self.required_admin = required_admin


RULE_MAPPING = {
    UUID("492345de-8d4a-45b6-8b94-d219f2b0c3e9"): RuleMetadata(
        function=compute_finale_phase_from_group_rank,
        attribute="compute_finale_phase_from_group_rank",
    ),
}

# Static check to make sure RULE_MAPPING and Rules attributes are same
rule_mapping_attributes = {rule_metadata.attribute for rule_metadata in RULE_MAPPING.values()}
rule_class_attributes = set(Rules.model_fields)

if rule_mapping_attributes != rule_class_attributes:  # pragma: no cover
    msg = (
        "RULE_MAPPING doesn't have the same attributes as Rules"
        f" class:\n{rule_mapping_attributes}\n{rule_class_attributes}"
    )
    raise ValueError(msg)
