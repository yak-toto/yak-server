from collections.abc import Callable
from dataclasses import dataclass
from uuid import UUID

from pydantic import BaseModel
from sqlalchemy.orm import Session

from yak_server.database.models import UserModel

from .compute_final_from_rank import (
    RuleComputeFinaleFromGroupRank,
    compute_finale_phase_from_group_rank,
)
from .compute_points import RuleComputePoints
from .compute_points import compute_points as compute_points_func


class Rules(BaseModel):
    compute_finale_phase_from_group_rank: RuleComputeFinaleFromGroupRank | None = None
    compute_points: RuleComputePoints | None = None


@dataclass(frozen=True, kw_only=True)
class RuleMetadata:
    function: (
        Callable[[Session, UserModel, RuleComputeFinaleFromGroupRank], tuple[int, str]]
        | Callable[[Session, UserModel, RuleComputePoints], tuple[int, str]]
    )
    attribute: str
    required_admin: bool = False


RULE_MAPPING = {
    UUID("492345de-8d4a-45b6-8b94-d219f2b0c3e9"): RuleMetadata(
        function=compute_finale_phase_from_group_rank,
        attribute="compute_finale_phase_from_group_rank",
    ),
    UUID("62d46542-8cf1-4a3b-af77-a5086f10ac59"): RuleMetadata(
        function=compute_points_func,
        attribute="compute_points",
        required_admin=True,
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
