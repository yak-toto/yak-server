from flask import Blueprint
from flask import request

from . import db
from .models import Matches
from .models import Scores
from .utils.auth_utils import token_required
from .utils.constants import GLOBAL_ENDPOINT
from .utils.constants import VERSION
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
            (
                match.to_dict()
                for match in Scores.query.filter_by(user_id=current_user.id)
            ),
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
    match = Scores.query.filter_by(user_id=current_user.id, match_id=match_id).first()
    if not match:
        return failed_response(404, "This match doesn't exist.")

    is_match_modified = False
    if request.method == "POST":
        body = request.get_json()
        results = body.get("results", [])
        if len(results) == 2:
            if match.score1 != results[0].get("score") or match.score2 != results[
                1
            ].get("score"):
                match.score1 = results[0].get("score")
                match.score2 = results[1].get("score")
                db.session.add(match)
                db.session.commit()
                is_match_modified = True
        else:
            return failed_response(401, "Wrong inputs")

    match_resource = match.to_dict()

    if is_match_modified:
        team1 = match_resource["results"][0]["team"]
        team2 = match_resource["results"][1]["team"]
        send_message(
            f"User {current_user.name} update match {team1} - "
            f"{team2} with the score {match.score1} - {match.score2}."
        )

    return success_response(200, match_resource)
