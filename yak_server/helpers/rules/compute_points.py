from itertools import chain
from typing import TYPE_CHECKING

from pydantic import BaseModel
from sqlalchemy import and_

from yak_server.database.models import (
    BinaryBetModel,
    GroupModel,
    MatchModel,
    PhaseModel,
    ScoreBetModel,
    UserModel,
)
from yak_server.helpers.group_position import get_group_rank_with_code

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


class RuleComputePoints(BaseModel):
    base_correct_result: int
    multiplying_factor_correct_result: int
    base_correct_score: int
    multiplying_factor_correct_score: int
    team_qualified: int
    first_team_qualified: int


def compute_points(db: "Session", admin: "UserModel", rule_config: RuleComputePoints) -> None:
    results = []

    for real_score in admin.score_bets:
        number_correct_result = 0
        number_correct_score = 0
        user_ids_found_correct_result = []
        user_ids_found_correct_score = []

        for user_score in (
            db.query(ScoreBetModel)
            .join(ScoreBetModel.match)
            .filter(
                and_(
                    ScoreBetModel.user_id != admin.id,
                    MatchModel.index == real_score.match.index,
                    MatchModel.group_id == real_score.match.group_id,
                ),
            )
        ):
            if user_score.is_same_results(real_score):
                number_correct_result += 1
                user_ids_found_correct_result.append(user_score.user_id)

                if user_score.is_same_scores(real_score):
                    number_correct_score += 1
                    user_ids_found_correct_score.append(user_score.user_id)

        results.append(
            {
                "number_correct_result": number_correct_result,
                "user_ids_found_correct_result": user_ids_found_correct_result,
                "number_correct_score": number_correct_score,
                "user_ids_found_correct_score": user_ids_found_correct_score,
            },
        )

    result_groups = {}

    other_users = db.query(UserModel).filter(UserModel.name != "admin")

    for group in (
        db.query(GroupModel)
        .join(GroupModel.phase)
        .filter(
            PhaseModel.code == "GROUP",
        )
    ):
        group_result_admin = get_group_rank_with_code(db, admin, group.id)

        if all_results_filled_in_group(group_result_admin):
            admin_first_team_id = group_result_admin[0].team.id
            admin_second_team_id = group_result_admin[1].team.id

            for other_user in other_users:
                if other_user.id not in result_groups:
                    result_groups[other_user.id] = {
                        "number_qualified_teams_guess": 0,
                        "number_first_qualified_guess": 0,
                    }

                group_result_user = get_group_rank_with_code(db, other_user, group.id)

                if all_results_filled_in_group(group_result_user):
                    user_first_team_id = group_result_user[0].team.id
                    user_second_team_id = group_result_user[1].team.id

                    result_groups[other_user.id]["number_qualified_teams_guess"] += len(
                        {user_first_team_id, user_second_team_id}
                        & {admin_first_team_id, admin_second_team_id},
                    )

                    if user_first_team_id == admin_first_team_id:
                        result_groups[other_user.id]["number_first_qualified_guess"] += 1

    quarter_finals_team = team_from_group_code(admin, "4")
    semi_finals_team = team_from_group_code(admin, "2")
    final_team = team_from_group_code(admin, "1")
    winner = winner_from_user(admin)

    numbers_of_players = other_users.count()

    for user in other_users:
        user.number_score_guess = 0
        user.number_match_guess = 0
        user.points = 0

        for result in results:
            if user.id in result["user_ids_found_correct_result"]:
                user.number_match_guess += 1
                user.points += (
                    rule_config.base_correct_result
                    + rule_config.multiplying_factor_correct_result
                    * (numbers_of_players - result["number_correct_result"])
                    / (numbers_of_players - 1)
                )

            if user.id in result["user_ids_found_correct_score"]:
                user.number_score_guess += 1
                user.points += (
                    rule_config.base_correct_score
                    + rule_config.multiplying_factor_correct_score
                    * (numbers_of_players - result["number_correct_score"])
                    / (numbers_of_players - 1)
                )

        user.number_qualified_teams_guess = result_groups.get(user.id, {}).get(
            "number_qualified_teams_guess",
            0,
        )
        user.number_first_qualified_guess = result_groups.get(user.id, {}).get(
            "number_first_qualified_guess",
            0,
        )

        user.points += user.number_qualified_teams_guess * rule_config.team_qualified
        user.points += user.number_first_qualified_guess * rule_config.first_team_qualified

        user.number_quarter_final_guess = len(
            team_from_group_code(user, "4").intersection(quarter_finals_team),
        )
        user.number_semi_final_guess = len(
            team_from_group_code(user, "2").intersection(semi_finals_team),
        )
        user.number_final_guess = len(
            team_from_group_code(user, "1").intersection(final_team),
        )
        user.number_winner_guess = len(winner_from_user(user).intersection(winner))

        user.points += 30 * user.number_quarter_final_guess
        user.points += 60 * user.number_semi_final_guess
        user.points += 120 * user.number_final_guess
        user.points += 200 * user.number_winner_guess

    db.commit()


def all_results_filled_in_group(group_result: list) -> bool:
    return all(team.played == len(group_result) - 1 for team in group_result)


def team_from_group_code(user: UserModel, group_code: str) -> set:
    return set(
        chain(
            *(
                (bet.match.team1.id, bet.match.team2.id)
                for bet in user.binary_bets.filter(GroupModel.code == group_code)
                .join(BinaryBetModel.match)
                .join(MatchModel.group)
                if bet.match.team1 is not None and bet.match.team2 is not None
            ),
        ),
    )


def winner_from_user(user: UserModel) -> set:
    finale_bet = list(
        user.binary_bets.filter(GroupModel.code == "1")
        .join(BinaryBetModel.match)
        .join(MatchModel.group),
    )

    if not finale_bet:
        return set()

    finale_bet = finale_bet[0]

    if finale_bet.is_one_won is None:
        return set()

    return {
        finale_bet.match.team1.id if finale_bet.is_one_won else finale_bet.match.team2.id,
    }