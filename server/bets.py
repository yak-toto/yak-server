from flask import Blueprint
from flask import request
from sqlalchemy import and_

from . import db
from .models import is_locked
from .models import Matches
from .models import Phase
from .models import Scores
from .utils.auth_utils import token_required
from .utils.constants import GLOBAL_ENDPOINT
from .utils.constants import VERSION
from .utils.errors import locked_bets
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
            key=lambda score: (score["phase"]["code"], score["index"]),
        ),
    )


@bets.route(f"/{GLOBAL_ENDPOINT}/{VERSION}/bets/groups/<string:phase_code>")
@token_required
def group_get(current_user, phase_code):
    phase = Phase.query.filter_by(code=phase_code).first()

    matches = Matches.query.filter_by(phase_id=phase.id)

    scores = Scores.query.filter(
        and_(
            Scores.user_id == current_user.id,
            Scores.match_id.in_(match.id for match in matches),
        )
    )

    return success_response(
        200,
        sorted(
            (score.to_dict() for score in scores),
            key=lambda score: score["index"],
        ),
    )


@bets.route(
    f"/{GLOBAL_ENDPOINT}/{VERSION}/bets/scores/<string:match_id>",
    methods=["PATCH", "GET"],
)
@token_required
def match_get(current_user, match_id):
    score = Scores.query.filter_by(user_id=current_user.id, match_id=match_id).first()
    if not score:
        return failed_response(*match_not_found)

    is_score_modified = False
    if request.method == "PATCH":
        if is_locked(score):
            return failed_response(*locked_bets)

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
        team1 = score_resource["team1"]["description"]
        team2 = score_resource["team2"]["description"]
        send_message(
            f"User {current_user.name} update match {team1} - "
            f"{team2} with the score {score.score1} - {score.score2}."
        )

    return success_response(200, score_resource)
