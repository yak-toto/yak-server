from flask import Blueprint
from flask import request

from . import db
from .auth_utils import token_required
from .constants import GLOBAL_ENDPOINT
from .constants import VERSION
from .models import Match
from .models import Matches
from .telegram_sender import send_message
from .utils import failed_response
from .utils import success_response

group = Blueprint("group", __name__)


@group.route(f"/{GLOBAL_ENDPOINT}/{VERSION}/bets/scores")
@token_required
def groups(current_user):
    return success_response(
        200,
        [match.to_dict() for match in Match.query.filter_by(user_id=current_user.id)],
    )


@group.route(f"/{GLOBAL_ENDPOINT}/{VERSION}/bets/groups/<string:group_name>")
@token_required
def group_get(current_user, group_name):
    matches = Matches.query.filter_by(group_name=group_name)

    group_resource = (
        Match.query.filter_by(user_id=current_user.id, match_id=match.id).first()
        for match in matches
    )

    return success_response(200, [match.to_dict() for match in group_resource])


@group.route(f"/{GLOBAL_ENDPOINT}/{VERSION}/groups/names")
@token_required
def groups_names(current_user):
    return success_response(
        200, sorted(list({match.group_name for match in Matches.query.all()}))
    )


@group.route(
    f"/{GLOBAL_ENDPOINT}/{VERSION}/bets/scores/<string:match_id>",
    methods=["POST", "GET"],
)
@token_required
def match_get(current_user, match_id):
    match = Match.query.filter_by(user_id=current_user.id, match_id=match_id).first()
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


@group.route(f"/{GLOBAL_ENDPOINT}/{VERSION}/matches", methods=["POST", "GET"])
@token_required
def matches(current_user):
    if current_user.name == "admin":
        if request.method == "POST":
            body = request.get_json()

            if Matches.query.first():
                return failed_response(409, "Resource already exising")

            for group in body:
                for match in group["matches"]:
                    db.session.add(
                        Matches(
                            group_name=group["group_name"],
                            team1=match["teams"][0],
                            team2=match["teams"][1],
                        )
                    )

            db.session.commit()

        return success_response(
            201 if request.method == "POST" else 200,
            [match.to_dict() for match in Matches.query.all()],
        )

    else:
        return failed_response(401, "Unauthorized access to admin API")
