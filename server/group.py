from flask import Blueprint
from flask import jsonify
from flask import request

from . import db
from .auth_utils import token_required
from .constants import GLOBAL_ENDPOINT
from .constants import VERSION
from .models import Match
from .models import Matches
from .telegram_sender import send_message

group = Blueprint("group", __name__)


@group.route(f"/{GLOBAL_ENDPOINT}/{VERSION}/groups")
@token_required
def groups(current_user):
    user_resource = list(Match.query.filter_by(user_id=current_user.id))

    results = {}
    for match in user_resource:
        results.setdefault(match.group_name, []).append(match.to_dict())

    return jsonify(results), 200


@group.route(f"/{GLOBAL_ENDPOINT}/{VERSION}/groups/<string:group_name>")
@token_required
def group_get(current_user, group_name):
    matches = Matches.query.filter_by(group_name=group_name)

    group_resource = (
        Match.query.filter_by(user_id=current_user.id, match_id=match.id).first()
        for match in matches
    )

    return (
        jsonify([match.to_dict() for match in group_resource]),
        200,
    )


@group.route(
    f"/{GLOBAL_ENDPOINT}/{VERSION}/groups/<string:group_name>", methods=["POST"]
)
@token_required
def group_post(current_user, group_name):
    body = request.get_json()

    matches = Match.query.filter_by(user_id=current_user.id, group_name=group_name)

    for index, match in enumerate(matches):
        if (
            match.score1 != body[index][0]["score"]
            or match.score2 != body[index][1]["score"]
        ):
            match.score1 = body[index][0]["score"]
            match.score2 = body[index][1]["score"]
            send_message(
                f"User {current_user.name} update match {match.team1} - "
                f"{match.team2} with the score {match.score1} - {match.score2}."
            )
            db.session.add(match)

    db.session.commit()

    return jsonify(body), 201


@group.route(f"/{GLOBAL_ENDPOINT}/{VERSION}/groups/names")
@token_required
def groups_names(current_user):
    return (
        jsonify(sorted(list({match.group_name for match in Matches.query.all()}))),
        200,
    )


@group.route(
    f"/{GLOBAL_ENDPOINT}/{VERSION}/match/<string:match_id>", methods=["POST", "GET"]
)
@token_required
def match_get(current_user, match_id):
    match = Match.query.filter_by(user_id=current_user.id, match_id=match_id).first()
    if not match:
        return (
            jsonify(
                {
                    "message": "This match doesn't exist. "
                    "Either it doesn't exist, either you are using the wrong user."
                }
            ),
            404,
        )

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
            return jsonify({"message": "Wrong inputs"}), 401

    match_resource = match.to_dict()
    team1 = match_resource["results"][0]["team"]
    team2 = match_resource["results"][1]["team"]
    if is_match_modified:
        send_message(
            f"User {current_user.name} update match {team1} - "
            f"{team2} with the score {match.score1} - {match.score2}."
        )

    return jsonify(match_resource), 200


@group.route(f"/{GLOBAL_ENDPOINT}/{VERSION}/matches", methods=["POST", "GET"])
@token_required
def matches(current_user):
    if current_user.name == "admin":
        if request.method == "POST":
            body = request.get_json()

            if Matches.query.first():
                return jsonify("resource already exising"), 409

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

        return (
            jsonify([match.to_dict() for match in Matches.query.all()]),
            201 if request.method == "POST" else 200,
        )

    else:
        return jsonify("Unauthorized access to admin api"), 401
