from itertools import chain
from typing import TYPE_CHECKING

from fastapi import status
from pydantic import BaseModel
from sqlalchemy.orm import selectinload

from yak_server.database.models import BinaryBetModel, GroupModel, MatchModel, PhaseModel
from yak_server.helpers.group_position import get_group_rank_with_code

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

    from yak_server.database.models import GroupPositionModel, UserModel


THIRD_PLACE_RANK = 3


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
    third_place_lookup: dict[str, list[str]] | None = None
    third_place_matchup: list[int] | None = None


def _resolve_third_place_assignment(
    groups_result: dict[str, list["GroupPositionModel"]],
    third_place_lookup: dict[str, list[str]],
    third_place_matchup: list[int],
) -> dict[int, str]:
    """Return {match_index: group_code} for the best 8 third-place teams.

    Zips the lookup list (e.g. ["3E", "3J", ...]) with third_place_matchup
    (e.g. [11, 15, ...]) so that position i → group "3X"[1:] plays in match
    third_place_matchup[i].

    Returns:
        dict mapping match index to group code, or empty dict when the group
        stage is not yet complete.
    """
    if not all(
        all(team.played == len(ranking) - 1 for team in ranking)
        for ranking in groups_result.values()
    ):
        return {}
    third_place_teams = sorted(
        (
            (code, ranking[THIRD_PLACE_RANK - 1])
            for code, ranking in groups_result.items()
            if len(ranking) >= THIRD_PLACE_RANK
        ),
        key=lambda x: (x[1].points, x[1].goals_difference, x[1].goals_for),
        reverse=True,
    )
    qualified_groups = sorted(code for code, _ in third_place_teams[:8])
    assignments = third_place_lookup["".join(qualified_groups)]
    return {
        match_idx: group_code[1:]  # "3X" → "X"
        for group_code, match_idx in zip(assignments, third_place_matchup, strict=True)
    }


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

    # A "dynamic" slot has an empty group field; the actual group is resolved
    # from the best 8 third-place teams across all groups.
    third_place_assignment: dict[int, str] = (
        _resolve_third_place_assignment(
            groups_result,
            rule_config.third_place_lookup,
            rule_config.third_place_matchup,
        )
        if rule_config.third_place_lookup is not None
        and rule_config.third_place_matchup is not None
        else {}
    )

    for index, match_config in enumerate(rule_config.versus, 1):
        team1_config = match_config.team1
        team2_config = match_config.team2

        team1_is_dynamic = team1_config.rank == THIRD_PLACE_RANK and not team1_config.group
        team2_is_dynamic = team2_config.rank == THIRD_PLACE_RANK and not team2_config.group

        if team1_is_dynamic or team2_is_dynamic:
            # Dynamic match: skip until all groups are complete and lookup is resolved
            if index not in third_place_assignment:
                continue
            resolved_group = third_place_assignment[index]
            team1_group = resolved_group if team1_is_dynamic else team1_config.group
            team2_group = resolved_group if team2_is_dynamic else team2_config.group
        else:
            team1_group = team1_config.group
            team2_group = team2_config.group
            if not all(
                team.played == len(groups_result[team1_group]) - 1
                for team in chain(
                    groups_result[team1_group],
                    groups_result[team2_group],
                )
            ):
                continue

        team1 = groups_result[team1_group][team1_config.rank - 1].team
        team2 = groups_result[team2_group][team2_config.rank - 1].team

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
