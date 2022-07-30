from flask import Blueprint
from flask import request

from . import db
from .models import Matches
from .models import Scores
from .utils.auth_utils import token_required
from .utils.constants import GLOBAL_ENDPOINT
from .utils.constants import VERSION
from .utils.errors import match_not_found
from .utils.errors import wrong_inputs
from .utils.flask_utils import failed_response
from .utils.flask_utils import success_response
from .utils.telegram_sender import send_message

bets = Blueprint("bets", __name__)


@bets.route(f"/{GLOBAL_ENDPOINT}/{VERSION}/bets/scores")
@token_required
def groups(current_user):
    return success_response(
        200,
        sorted(
            (score.to_dict() for score in current_user.scores),
            key=lambda score: (score["group_name"], score["match_index"]),
        ),
    )


@bets.route(f"/{GLOBAL_ENDPOINT}/{VERSION}/bets/groups/<string:group_name>")
@token_required
def group_get(current_user, group_name):
    matches = Matches.query.filter_by(group_name=group_name)

    group_resource = (
        Scores.query.filter_by(user_id=current_user.id, match_id=match.id).first()
        for match in matches
    )

    return success_response(
        200,
        sorted(
            (match.to_dict() for match in group_resource),
            key=lambda score: score["match_index"],
        ),
    )


@bets.route(
    f"/{GLOBAL_ENDPOINT}/{VERSION}/bets/scores/<string:match_id>",
    methods=["POST", "GET"],
)
@token_required
def match_get(current_user, match_id):
    score = Scores.query.filter_by(user_id=current_user.id, match_id=match_id).first()
    if not score:
        return failed_response(*match_not_found)

    is_score_modified = False
    if request.method == "POST":
        body = request.get_json()
        if "team1" in body and "team2" in body:
            if score.score1 != body["team1"].get("score") or score.score2 != body[
                "team2"
            ].get("score"):
                score.score1 = body["team1"].get("score")
                score.score2 = body["team2"].get("score")
                db.session.add(score)
                db.session.commit()
                is_score_modified = True
        else:
            return failed_response(*wrong_inputs)

    score_resource = score.to_dict()

    if is_score_modified:
        team1 = score_resource["team1"]["name"]
        team2 = score_resource["team2"]["name"]
        send_message(
            f"User {current_user.name} update match {team1} - "
            f"{team2} with the score {score.score1} - {score.score2}."
        )

    return success_response(200, score_resource)
