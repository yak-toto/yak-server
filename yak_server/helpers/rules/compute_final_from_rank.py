from itertools import chain
from typing import TYPE_CHECKING

from pydantic import BaseModel
from sqlmodel import Session, select

from yak_server.database.models3 import BinaryBetModel, GroupModel, MatchModel, PhaseModel
from yak_server.helpers.group_position import get_group_rank_with_code

if TYPE_CHECKING:
    from sqlmodel import Session

    from yak_server.database.models3 import UserModel


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
    session: "Session",
    user: "UserModel",
    rule_config: RuleComputeFinaleFromGroupRank,
) -> None:
    first_phase_phase_group = session.exec(
        select(GroupModel).where(GroupModel.code == rule_config.to_group)
    ).first()

    groups_result = {
        group.code: get_group_rank_with_code(session, user, group.id)
        for group in session.exec(
            select(GroupModel)
            .join(GroupModel.phase)
            .where(
                PhaseModel.code == rule_config.from_phase,
            )
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

            binary_bet = session.exec(
                select(BinaryBetModel)
                .join(BinaryBetModel.match)
                .where(
                    MatchModel.index == index,
                    MatchModel.user_id == user.id,
                    MatchModel.group_id == first_phase_phase_group.id,
                )
            ).first()

            binary_bet.match.team1_id = team1.id
            binary_bet.match.team2_id = team2.id

            session.flush()

    session.commit()
