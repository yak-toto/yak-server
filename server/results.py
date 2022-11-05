from flask import Blueprint
from flask import current_app
from sqlalchemy import and_

from . import db
from .models import ScoreBet
from .models import User
from .utils.auth_utils import token_required
from .utils.constants import GLOBAL_ENDPOINT
from .utils.constants import VERSION
from .utils.errors import no_results_for_admin_user
from .utils.errors import unauthorized_access_to_admin_api
from .utils.flask_utils import failed_response
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
        return failed_response(*no_results_for_admin_user)

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
        return failed_response(*unauthorized_access_to_admin_api)


def compute_points(
    base_correct_result,
    multiplying_factor_correct_result,
    base_correct_score,
    multiplying_factor_correct_score,
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

    users = User.query.filter(User.name != "admin")
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

    db.session.commit()
