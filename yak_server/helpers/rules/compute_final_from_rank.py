from itertools import chain
from typing import TYPE_CHECKING

from fastapi import status
from pydantic import BaseModel
from sqlalchemy.orm import selectinload

from yak_server.database.models import BinaryBetModel, GroupModel, MatchModel, PhaseModel
from yak_server.helpers.group_position import get_group_rank_with_code

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

    from yak_server.database.models import UserModel


class Team(BaseModel):
    rank: int
    group: str


class Versus(BaseModel):
    team1: Team
    team2: Team


class RuleComputeFinaleFromGroupRank(BaseModel):
    to_group: str
    from_phase: str
    versus: list[Versus]


def compute_finale_phase_from_group_rank(
    db: "Session",
    user: "UserModel",
    rule_config: RuleComputeFinaleFromGroupRank,
) -> tuple[int, str]:
    first_phase_group = db.query(GroupModel).filter_by(code=rule_config.to_group).first()

    if first_phase_group is None:
        return status.HTTP_404_NOT_FOUND, f"Group not found with code: {rule_config.to_group}"

    groups_result = {
        group.code: get_group_rank_with_code(db, user, group.id)
        for group in db
        .query(GroupModel)
        .join(GroupModel.phase)
        .where(
            PhaseModel.code == rule_config.from_phase,
        )
    }

    for index, match_config in enumerate(rule_config.versus, 1):
        if all(
            team.played == len(groups_result[match_config.team1.group]) - 1
            for team in chain(
                groups_result[match_config.team1.group],
                groups_result[match_config.team2.group],
            )
        ):
            team1 = groups_result[match_config.team1.group][match_config.team1.rank - 1].team
            team2 = groups_result[match_config.team2.group][match_config.team2.rank - 1].team

            binary_bet = (
                db
                .query(BinaryBetModel)
                .options(selectinload(BinaryBetModel.match))
                .join(BinaryBetModel.match)
                .where(
                    MatchModel.index == index,
                    MatchModel.user_id == user.id,
                    MatchModel.group_id == first_phase_group.id,
                )
                .first()
            )

            if binary_bet is not None:
                binary_bet.match.team1_id = team1.id
                binary_bet.match.team2_id = team2.id

            db.flush()

    db.commit()

    return status.HTTP_200_OK, ""
