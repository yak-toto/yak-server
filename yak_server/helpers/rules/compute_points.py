from collections.abc import Iterable
from dataclasses import dataclass, field
from itertools import chain
from typing import TYPE_CHECKING
from uuid import UUID

from pydantic import BaseModel
from sqlmodel import func, select

from yak_server.database.models3 import (
    BinaryBetModel,
    GroupModel,
    MatchModel,
    PhaseModel,
    ScoreBetModel,
    UserModel,
)
from yak_server.helpers.group_position import get_group_rank_with_code

if TYPE_CHECKING:
    from sqlmodel import Session


class RuleComputePoints(BaseModel):
    base_correct_result: int
    multiplying_factor_correct_result: int
    base_correct_score: int
    multiplying_factor_correct_score: int
    team_qualified: int
    first_team_qualified: int


@dataclass
class ResultForScoreBet:
    number_correct_result: int = 0
    user_ids_found_correct_result: list[UUID] = field(default_factory=list)
    number_correct_score: int = 0
    user_ids_found_correct_score: list[UUID] = field(default_factory=list)


def compute_results_for_score_bet(session: "Session", admin: UserModel) -> list[ResultForScoreBet]:
    results: list[ResultForScoreBet] = []

    for real_score, _ in session.exec(
        select(ScoreBetModel, MatchModel).where(MatchModel.user_id == admin.id)
    ):
        result_for_score_bet = ResultForScoreBet()

        for user_score, _ in session.exec(
            select(ScoreBetModel, MatchModel).where(
                MatchModel.user_id != admin.id,
                MatchModel.index == real_score.match.index,
                MatchModel.group_id == real_score.match.group_id,
            )
        ):
            if user_score.is_same_results(real_score):
                result_for_score_bet.number_correct_result += 1
                result_for_score_bet.user_ids_found_correct_result.append(user_score.match.user_id)

                if user_score.is_same_scores(real_score):
                    result_for_score_bet.number_correct_score += 1
                    result_for_score_bet.user_ids_found_correct_score.append(
                        user_score.match.user_id
                    )

        results.append(result_for_score_bet)

    return results


@dataclass
class ResultForGroupRank:
    number_qualified_teams_guess: int = 0
    number_first_qualified_guess: int = 0


def all_results_filled_in_group(group_result: list) -> bool:
    return all(team.played == len(group_result) - 1 for team in group_result)


def compute_results_for_group_rank(
    session: "Session", admin: UserModel, other_users: Iterable[UserModel]
) -> dict[UUID, ResultForGroupRank]:
    result_groups: dict[UUID, ResultForGroupRank] = {}

    for group, _ in session.exec(select(GroupModel, PhaseModel).where(PhaseModel.code == "GROUP")):
        group_result_admin = get_group_rank_with_code(session, admin, group.id)

        if all_results_filled_in_group(group_result_admin):
            admin_first_team_id = group_result_admin[0].team.id
            admin_second_team_id = group_result_admin[1].team.id

            for other_user in other_users:
                if other_user.id not in result_groups:
                    result_groups[other_user.id] = ResultForGroupRank()

                group_result_user = get_group_rank_with_code(session, other_user, group.id)

                if all_results_filled_in_group(group_result_user):
                    user_first_team_id = group_result_user[0].team.id
                    user_second_team_id = group_result_user[1].team.id

                    result_groups[other_user.id].number_qualified_teams_guess += len(
                        {user_first_team_id, user_second_team_id}
                        & {admin_first_team_id, admin_second_team_id},
                    )

                    if user_first_team_id == admin_first_team_id:
                        result_groups[other_user.id].number_first_qualified_guess += 1

    return result_groups


def team_from_group_code(session: "Session", user: UserModel, group_code: str) -> set:
    return set(
        chain(
            *(
                (bet.match.team1_id, bet.match.team2_id)
                for bet, _, _ in session.exec(
                    select(BinaryBetModel, MatchModel, GroupModel).where(
                        MatchModel.user_id == user.id, GroupModel.code == group_code
                    )
                )
                if bet.match.team1_id is not None and bet.match.team2_id is not None
            ),
        ),
    )


def winner_from_user(session: "Session", user: UserModel) -> set:
    finale_bet, _, _ = next(
        iter(
            session.exec(
                select(BinaryBetModel, MatchModel, GroupModel).where(
                    MatchModel.user_id == user.id, GroupModel.code == "1"
                )
            )
        )
    )

    if finale_bet.is_one_won is None:
        return set()

    return {
        finale_bet.match.team1_id if finale_bet.is_one_won else finale_bet.match.team2_id,
    }


def compute_points(session: "Session", admin: UserModel, rule_config: RuleComputePoints) -> None:
    results = compute_results_for_score_bet(session, admin)

    other_users = session.exec(select(UserModel).where(UserModel.name != "admin"))

    result_groups: dict[UUID, ResultForGroupRank] = compute_results_for_group_rank(
        session,
        admin,
        other_users,
    )

    quarter_finals_team = team_from_group_code(session, admin, "4")
    semi_finals_team = team_from_group_code(session, admin, "2")
    final_team = team_from_group_code(session, admin, "1")
    winner = winner_from_user(session, admin)

    numbers_of_players = (
        session.query(UserModel)
        .with_entities(func.count())
        .where(UserModel.name != "admin")
        .scalar()
    )

    for user in other_users:
        user.number_score_guess = 0
        user.number_match_guess = 0
        user.points = 0

        for result in results:
            if user.id in result.user_ids_found_correct_result:
                user.number_match_guess += 1
                user.points += (
                    rule_config.base_correct_result
                    + rule_config.multiplying_factor_correct_result
                    * (numbers_of_players - result.number_correct_result)
                    / (numbers_of_players - 1)
                )

            if user.id in result.user_ids_found_correct_score:
                user.number_score_guess += 1
                user.points += (
                    rule_config.base_correct_score
                    + rule_config.multiplying_factor_correct_score
                    * (numbers_of_players - result.number_correct_score)
                    / (numbers_of_players - 1)
                )

        if user.id not in result_groups:
            continue

        user.number_qualified_teams_guess = result_groups[user.id].number_qualified_teams_guess
        user.number_first_qualified_guess = result_groups[user.id].number_first_qualified_guess

        user.points += user.number_qualified_teams_guess * rule_config.team_qualified
        user.points += user.number_first_qualified_guess * rule_config.first_team_qualified

        user.number_quarter_final_guess = len(
            team_from_group_code(session, user, "4").intersection(quarter_finals_team),
        )
        user.number_semi_final_guess = len(
            team_from_group_code(session, user, "2").intersection(semi_finals_team),
        )
        user.number_final_guess = len(
            team_from_group_code(session, user, "1").intersection(final_team),
        )
        user.number_winner_guess = len(winner_from_user(session, user).intersection(winner))

        user.points += 30 * user.number_quarter_final_guess
        user.points += 60 * user.number_semi_final_guess
        user.points += 120 * user.number_final_guess
        user.points += 200 * user.number_winner_guess

    session.commit()
