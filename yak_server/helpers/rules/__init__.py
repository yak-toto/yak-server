from typing import Optional
from uuid import UUID

from pydantic import BaseModel

from .compute_final_from_rank import (
    RuleComputeFinaleFromGroupRank,
    compute_finale_phase_from_group_rank,
)


class Rules(BaseModel):
    compute_finale_phase_from_group_rank: Optional[RuleComputeFinaleFromGroupRank] = None


RULE_MAPPING = {
    UUID("492345de-8d4a-45b6-8b94-d219f2b0c3e9"): (
        compute_finale_phase_from_group_rank,
        "compute_finale_phase_from_group_rank",
    ),
}

# Static check to make sure RULE_MAPPING and RULES attributes are same
rule_mapping_attributes = {attr_rule for _, attr_rule in RULE_MAPPING.values()}
rule_class_attributes = set(Rules.model_fields)
if rule_mapping_attributes != rule_class_attributes:
    msg = (
        "RULE_MAPPING doesn't have the same attributes as Rules"
        f" class:\n{rule_mapping_attributes}\n{rule_class_attributes}"
    )
    raise ValueError(msg)
