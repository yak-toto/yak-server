import json

from flask import Blueprint
from flask import jsonify
from flask import request

from . import db
from .auth_utils import token_required
from .constants import GLOBAL_ENDPOINT
from .constants import VERSION
from .models import Match
from .telegram_sender import send_message

group = Blueprint("group", __name__)

with open("server/matches.json") as file:
    matches = json.load(file)
    GROUPS = tuple(matches.keys())


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
    if group_name not in GROUPS:
        return "bad request!", 404

    group_resource = Match.query.filter_by(
        user_id=current_user.id, group_name=group_name
    )

    return (
        jsonify([match.to_dict() for match in group_resource]),
        200,
    )


@group.route(
    f"/{GLOBAL_ENDPOINT}/{VERSION}/groups/<string:group_name>", methods=["POST"]
)
@token_required
def group_post(current_user, group_name=None):
    if group_name not in GROUPS:
        return "bad request!", 404

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
def groups_names():
    return jsonify(GROUPS), 200


@group.route(f"/{GLOBAL_ENDPOINT}/{VERSION}/match/<string:id>", methods=["POST", "GET"])
@token_required
def match_get(current_user, id):
    match = Match.query.filter_by(user_id=current_user.id, id=id).first()
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

                send_message(
                    f"User {current_user.name} update match {match.team1} - "
                    f"{match.team2} with the score {match.score1} - {match.score2}."
                )
        else:
            return jsonify({"message": "Wrong inputs"}), 401

    return jsonify(match.to_dict()), 200
