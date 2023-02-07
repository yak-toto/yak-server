from itertools import chain

from flask import Blueprint, current_app
from sqlalchemy import and_

from yak_server import db
from yak_server.database.models import (
    BinaryBetModel,
    GroupModel,
    MatchModel,
    PhaseModel,
    ScoreBetModel,
    UserModel,
)

from .bets import get_result_with_group_code
from .utils.auth_utils import token_required
from .utils.constants import GLOBAL_ENDPOINT, VERSION
from .utils.errors import NoResultsForAdminUser, UnauthorizedAccessToAdminAPI
from .utils.flask_utils import success_response

results = Blueprint("results", __name__)


@results.get(f"/{GLOBAL_ENDPOINT}/{VERSION}/score_board")
@token_required
def score_board(current_user):
    return success_response(
        200,
        [
            user.to_result_dict()
            for user in UserModel.query.order_by(UserModel.points.desc()).filter(
                UserModel.name != "admin",
            )
        ],
    )


@results.get(f"/{GLOBAL_ENDPOINT}/{VERSION}/results")
@token_required
def results_get(current_user):
    if current_user.name == "admin":
        raise NoResultsForAdminUser

    results = UserModel.query.order_by(UserModel.points.desc()).filter(
        UserModel.name != "admin",
    )

    rank = [
        index
        for index, user_result in enumerate(results, start=1)
        if user_result.id == current_user.id
    ][0]

    return success_response(
        200,
        UserModel.query.get(current_user.id).to_result_dict() | {"rank": rank},
    )


@results.post(f"/{GLOBAL_ENDPOINT}/{VERSION}/compute_points")
@token_required
def compute_points_post(current_user):
    if current_user.name != "admin":
        raise UnauthorizedAccessToAdminAPI

    compute_points(
        current_app.config["BASE_CORRECT_RESULT"],
        current_app.config["MULTIPLYING_FACTOR_CORRECT_RESULT"],
        current_app.config["BASE_CORRECT_SCORE"],
        current_app.config["MULTIPLYING_FACTOR_CORRECT_SCORE"],
        current_app.config["TEAM_QUALIFIED"],
        current_app.config["FIRST_TEAM_QUALIFIED"],
    )

    return success_response(
        200,
        [
            user.to_result_dict()
            for user in UserModel.query.order_by(UserModel.points.desc()).filter(
                UserModel.name != "admin",
            )
        ],
    )


def compute_points(
    base_correct_result,
    multiplying_factor_correct_result,
    base_correct_score,
    multiplying_factor_correct_score,
    team_qualified,
    first_team_qualified,
):
    admin = UserModel.query.filter_by(name="admin").first()

    results = []

    for real_score in admin.score_bets:
        number_correct_result = 0
        number_correct_score = 0
        user_ids_found_correct_result = []
        user_ids_found_correct_score = []

        for user_score in ScoreBetModel.query.filter(
            and_(
                ScoreBetModel.match_id == real_score.match_id,
                ScoreBetModel.user_id != admin.id,
            ),
        ):
            if user_score.is_same_results(real_score):
                number_correct_result += 1
                user_ids_found_correct_result.append(user_score.user_id)

                if user_score.is_same_scores(real_score):
                    number_correct_score += 1
                    user_ids_found_correct_score.append(user_score.user_id)

        results.append(
            {
                "match_id": real_score.match_id,
                "number_correct_result": number_correct_result,
                "user_ids_found_correct_result": user_ids_found_correct_result,
                "number_correct_score": number_correct_score,
                "user_ids_found_correct_score": user_ids_found_correct_score,
            },
        )

    result_groups = {}

    users = UserModel.query.filter(UserModel.name != "admin")

    for group in GroupModel.query.join(GroupModel.phase).filter(
        PhaseModel.code == "GROUP",
    ):
        group_result_admin = get_result_with_group_code(admin.id, group.code)["results"]

        if all_results_filled_in_group(group_result_admin):
            admin_first_team_id = group_result_admin[0]["id"]
            admin_second_team_id = group_result_admin[1]["id"]

            for user in users:
                if user.id not in result_groups:
                    result_groups[user.id] = {
                        "number_qualified_teams_guess": 0,
                        "number_first_qualified_guess": 0,
                    }

                group_result_user = get_result_with_group_code(user.id, group.code)["results"]

                if all_results_filled_in_group(group_result_user):
                    user_first_team_id = group_result_user[0]["id"]
                    user_second_team_id = group_result_user[1]["id"]

                    result_groups[user.id]["number_qualified_teams_guess"] += len(
                        {user_first_team_id, user_second_team_id}
                        & {admin_first_team_id, admin_second_team_id},
                    )

                    if user_first_team_id == admin_first_team_id:
                        result_groups[user.id]["number_first_qualified_guess"] += 1

    quarter_finals_team = team_from_group_code(admin, "4")
    semi_finals_team = team_from_group_code(admin, "2")
    final_team = team_from_group_code(admin, "1")
    winner = winner_from_user(admin)

    numbers_of_players = users.count()

    for user in users:
        user.number_score_guess = 0
        user.number_match_guess = 0
        user.points = 0

        for result in results:
            if user.id in result["user_ids_found_correct_result"]:
                user.number_match_guess += 1
                user.points += base_correct_result + multiplying_factor_correct_result * (
                    numbers_of_players - result["number_correct_result"]
                ) / (numbers_of_players - 1)

            if user.id in result["user_ids_found_correct_score"]:
                user.number_score_guess += 1
                user.points += base_correct_score + multiplying_factor_correct_score * (
                    numbers_of_players - result["number_correct_score"]
                ) / (numbers_of_players - 1)

        user.number_qualified_teams_guess = result_groups.get(user.id, {}).get(
            "number_qualified_teams_guess",
            0,
        )
        user.number_first_qualified_guess = result_groups.get(user.id, {}).get(
            "number_first_qualified_guess",
            0,
        )

        user.points += user.number_qualified_teams_guess * team_qualified
        user.points += user.number_first_qualified_guess * first_team_qualified

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

    db.session.commit()


def all_results_filled_in_group(group_result):
    return all(team["played"] == len(group_result) - 1 for team in group_result)


def team_from_group_code(user, group_code):
    return set(
        chain(
            *(
                (bet.match.team1.id, bet.match.team2.id)
                for bet in user.binary_bets.filter(GroupModel.code == group_code)
                .join(BinaryBetModel.match)
                .join(MatchModel.group)
            ),
        ),
    )


def winner_from_user(user):
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
