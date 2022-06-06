import json
from functools import wraps
from typing import Tuple

import jwt
from flask import Blueprint
from flask import current_app
from flask import jsonify
from flask import request
from sqlalchemy import select

from . import db
from .models import Match
from .models import User
from .telegram_sender import send_message

main = Blueprint("main", __name__)

with open("server/matches.json") as file:
    matches = json.load(file)
    GROUPS = tuple(matches.keys())


def token_required(f):
    @wraps(f)
    def _verify(*args, **kwargs):
        auth_headers = request.headers.get("Authorization", "").split()

        print(len(auth_headers))

        invalid_msg = {
            "message": "Invalid token. Registeration and / or authentication required",
            "authenticated": False,
        }
        expired_msg = {
            "message": "Expired token. Reauthentication required.",
            "authenticated": False,
        }

        if len(auth_headers) != 2:
            return jsonify(invalid_msg), 401

        try:
            token = auth_headers[1]
            print(current_app.config["SECRET_KEY"])
            data = jwt.decode(
                token, current_app.config["SECRET_KEY"], algorithms=["HS256"]
            )
            user = User.query.get(data["sub"])
            if not user:
                raise RuntimeError("User not found")
            return f(user, *args, **kwargs)
        except jwt.ExpiredSignatureError:
            return jsonify(expired_msg), 401  # 401 is Unauthorized HTTP status code
        except (jwt.InvalidTokenError, Exception) as e:
            print(e)
            return jsonify(invalid_msg), 401

    return _verify


@main.route("/groups")
@token_required
def groups(current_user):
    user_resource = list(Match.query.filter_by(user_id=current_user.id))

    results = {}
    for match in user_resource:
        results.setdefault(match.group_name, []).append(match.to_dict())

    return jsonify(results), 200


@main.route("/groups/<string:group_name>")
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


@main.route("/groups/<string:group_name>", methods=["POST"])
@token_required
def group_post(current_user, group_name=None):
    if group_name not in GROUPS:
        return "bad request!", 404

    body = request.get_json()

    matches = Match.query.filter_by(user_id=current_user.id, group_name=group_name)

    is_matches_modified = False
    for index, match in enumerate(matches):
        if (
            match.score1 != body[index][0]["score"]
            or match.score2 != body[index][1]["score"]
        ):
            is_matches_modified = True
            match.score1 = body[index][0]["score"]
            match.score2 = body[index][1]["score"]
            send_message(
                f"User {current_user.name} update match {match.team1} - "
                f"{match.team2} with the score {match.score1} - {match.score2}."
            )
            db.session.add(match)

    db.session.commit()

    if current_user.name == "admin" and is_matches_modified:
        compute_points()

    return jsonify(body), 201


@main.route("/groups/names")
def groups_names():
    return jsonify(GROUPS), 200


@main.route("/match", methods=["POST", "GET"])
@token_required
def match(current_user):
    team1 = request.args.get("team1")
    team2 = request.args.get("team2")

    if request.method == "POST":
        match = Match.query.filter_by(
            team1=team1, team2=team2, user_id=current_user.id
        ).first()
        body = request.get_json()
        match.score1, match.score2 = body
        db.session.add(match)
        db.session.commit()
        scores_resource = body
    else:
        query = select(Match.score1, Match.score2).filter_by(
            team1=team1, team2=team2, user_id=current_user.id
        )
        scores_resource = list(db.session.execute(query))[0]

    return jsonify([scores_resource[0], scores_resource[1]]), 200


@main.route("/match/<string:id>", methods=["POST", "GET"])
@token_required
def match_get(current_user, id=None):
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
        if (
            len(results) == 2
            and results[0].get("score") is not None
            and results[1].get("score") is not None
        ):
            match.score1 = results[0].get("score")
            match.score2 = results[1].get("score")
            db.session.add(match)
            db.session.commit()
        else:
            return jsonify({"message": "Wrong inputs"}), 401

    return jsonify(match.to_dict()), 200


@main.route("/score_board")
def score_board():
    query = (
        select(User.name, User.points)
        .order_by(User.points.desc())
        .filter(User.name != "admin")
    )
    score_board_resource = list(db.session.execute(query))

    return jsonify([list(t) for t in score_board_resource]), 200


def compute_points():
    users = User.query.filter(User.name != "admin")

    for user in users:
        points = 0
        user_matches = Match.query.filter_by(user_id=user.id)

        for match in user_matches:
            admin_match = Match.query.filter_by(
                name="admin", team1=match.team1, team2=match.team2
            ).first()

            if is_same_scores(
                (match.score1, match.score2), (admin_match.score1, admin_match.score2)
            ):
                points += 8
            elif is_same_resuls(
                (match.score1, match.score2), (admin_match.score1, admin_match.score2)
            ):
                points += 3

        user.points = points
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
