from flask import Blueprint
from flask import current_app
from sqlalchemy import and_

from . import db
from .bets import get_result_with_group_code
from .models import Group
from .models import Phase
from .models import ScoreBet
from .models import User
from .utils.auth_utils import token_required
from .utils.constants import GLOBAL_ENDPOINT
from .utils.constants import VERSION
from .utils.errors import NoResultsForAdminUser
from .utils.errors import UnauthorizedAccessToAdminAPI
from .utils.flask_utils import success_response

results = Blueprint("results", __name__)


@results.route(f"/{GLOBAL_ENDPOINT}/{VERSION}/score_board")
@token_required
def score_board(current_user):
    return success_response(
        200,
        [
            user.to_result_dict()
            for user in User.query.order_by(User.points.desc()).filter(
                User.name != "admin"
            )
        ],
    )


@results.route(f"/{GLOBAL_ENDPOINT}/{VERSION}/results")
@token_required
def results_get(current_user):
    if current_user.name == "admin":
        raise NoResultsForAdminUser()

    results = User.query.order_by(User.points.desc()).filter(User.name != "admin")

    rank = [
        index
        for index, user_result in enumerate(results, start=1)
        if user_result.id == current_user.id
    ][0]

    return success_response(
        200, User.query.get(current_user.id).to_result_dict() | {"rank": rank}
    )


@results.route(f"/{GLOBAL_ENDPOINT}/{VERSION}/compute_points", methods=["POST"])
@token_required
def compute_points_post(current_user):
    if current_user.name == "admin":
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
                for user in User.query.order_by(User.points.desc()).filter(
                    User.name != "admin"
                )
            ],
        )
    else:
        raise UnauthorizedAccessToAdminAPI()


def compute_points(
    base_correct_result,
    multiplying_factor_correct_result,
    base_correct_score,
    multiplying_factor_correct_score,
    team_qualified,
    first_team_qualified,
):
    admin = User.query.filter_by(name="admin").first()

    results = []

    for real_score in admin.bets:
        number_correct_result = 0
        number_correct_score = 0
        user_ids_found_correct_result = []
        user_ids_found_correct_score = []

        for user_score in ScoreBet.query.filter(
            and_(ScoreBet.match_id == real_score.match_id, ScoreBet.user_id != admin.id)
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
            }
        )

    result_groups = {}

    users = User.query.filter(User.name != "admin")

    for group in Group.query.join(Group.phase).filter(Phase.code == "GROUP"):
        group_result_admin = get_result_with_group_code(admin.id, group.code)["results"]

        if all(team["played"] == 3 for team in group_result_admin):
            admin_first_team_id = group_result_admin[0]["id"]
            admin_second_team_id = group_result_admin[1]["id"]

            for user in users:
                if user.id not in result_groups:
                    result_groups[user.id] = {
                        "number_qualified_teams_guess": 0,
                        "number_first_qualified_guess": 0,
                    }

                group_result_user = get_result_with_group_code(user.id, group.code)[
                    "results"
                ]

                if all(team["played"] == 3 for team in group_result_user):
                    user_first_team_id = group_result_user[0]["id"]
                    user_second_team_id = group_result_user[1]["id"]

                    result_groups[user.id]["number_qualified_teams_guess"] += len(
                        {user_first_team_id, user_second_team_id}
                        & {admin_first_team_id, admin_second_team_id}
                    )

                    if user_first_team_id == admin_first_team_id:
                        result_groups[user.id]["number_first_qualified_guess"] += 1

    numbers_of_players = users.count()

    for user in users:
        user.number_score_guess = 0
        user.number_match_guess = 0
        user.points = 0

        for result in results:
            if user.id in result["user_ids_found_correct_result"]:
                user.number_match_guess += 1
                user.points += (
                    base_correct_result
                    + multiplying_factor_correct_result
                    * (numbers_of_players - result["number_correct_result"])
                    / (numbers_of_players - 1)
                )

            if user.id in result["user_ids_found_correct_score"]:
                user.number_score_guess += 1
                user.points += base_correct_score + multiplying_factor_correct_score * (
                    numbers_of_players - result["number_correct_score"]
                ) / (numbers_of_players - 1)

        user.number_qualified_teams_guess = result_groups.get(user.id, {}).get(
            "number_qualified_teams_guess", 0
        )
        user.number_first_qualified_guess = result_groups.get(user.id, {}).get(
            "number_first_qualified_guess", 0
        )

        user.points += user.number_qualified_teams_guess * team_qualified
        user.points += user.number_first_qualified_guess * first_team_qualified

    db.session.commit()
