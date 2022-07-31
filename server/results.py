from typing import Tuple

from flask import Blueprint

from . import db
from .models import Scores
from .models import User
from .utils.auth_utils import token_required
from .utils.constants import GLOBAL_ENDPOINT
from .utils.constants import VERSION
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
    return success_response(200, User.query.get(current_user.id).to_result_dict())


@results.route(f"/{GLOBAL_ENDPOINT}/{VERSION}/compute_points", methods=["POST"])
@token_required
def compute_points_post(current_user):
    if current_user.name == "admin":
        compute_points()

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


def compute_points():
    users = User.query.filter(User.name != "admin")
    admin = User.query.filter_by(name="admin").first()

    for user in users:
        user_matches = Scores.query.filter_by(user_id=user.id)
        user.number_score_guess = 0
        user.number_match_guess = 0
        user.points = 0

        for match in user_matches:
            admin_match = Scores.query.filter_by(
                user_id=admin.id, match_id=match.match_id
            ).first()

            if is_same_scores(
                (match.score1, match.score2), (admin_match.score1, admin_match.score2)
            ):
                user.number_score_guess += 1
                user.number_match_guess += 1
            elif is_same_resuls(
                (match.score1, match.score2), (admin_match.score1, admin_match.score2)
            ):
                user.number_match_guess += 1

            user.points = (
                user.number_score_guess * 8
                + (user.number_match_guess - user.number_score_guess) * 3
            )

        db.session.add(user)

    db.session.commit()


def is_same_scores(user_score: Tuple[int, int], real_scores: Tuple[int, int]) -> bool:
    if None in (user_score + real_scores):
        return False
    return user_score == real_scores


def is_same_resuls(user_score: Tuple[int, int], real_scores: Tuple[int, int]) -> bool:
    return (
        (is_1_win(user_score) and is_1_win(real_scores))
        or (is_draw(user_score) and is_draw(real_scores))
        or (is_2_win(user_score) and is_2_win(real_scores))
    )


def is_1_win(scores: Tuple[int, int]) -> bool:
    if None in scores:
        return False
    return scores[0] > scores[1]


def is_draw(scores: Tuple[int, int]) -> bool:
    if None in scores:
        return False
    return scores[0] == scores[1]


def is_2_win(scores: Tuple[int, int]) -> bool:
    if None in scores:
        return False
    return scores[0] < scores[1]
