import json
from functools import wraps
from typing import Tuple

import jwt
from flask import Blueprint
from flask import current_app
from flask import jsonify
from flask import request

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


@main.route("/current_user")
@token_required
def current_user(current_user):
    return jsonify(current_user.to_user_dict()), 200


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


@main.route("/groups/names")
def groups_names():
    return jsonify(GROUPS), 200


@main.route("/match/<string:id>", methods=["POST", "GET"])
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

                if current_user.name == "admin":
                    compute_points()
        else:
            return jsonify({"message": "Wrong inputs"}), 401

    return jsonify(match.to_dict()), 200


@main.route("/score_board")
@token_required
def score_board(current_user):
    return (
        jsonify(
            [
                user.to_result_dict()
                for user in User.query.order_by(User.points.desc()).filter(
                    User.name != "admin"
                )
            ]
        ),
        200,
    )


@main.route("/results")
@token_required
def results(current_user):
    return (
        jsonify(User.query.filter_by(id=current_user.id).first().to_result_dict()),
        200,
    )


@main.route("/compute_points", methods=["POST"])
@token_required
def compute_points_post(current_user):
    if current_user.name == "admin":
        compute_points()

        return (
            jsonify(
                [
                    user.to_result_dict()
                    for user in User.query.order_by(User.points.desc()).filter(
                        User.name != "admin"
                    )
                ]
            ),
            200,
        )
    else:
        return jsonify("Unauthorized access to admin api"), 401


def compute_points():
    users = User.query.filter(User.name != "admin")
    admin = User.query.filter_by(name="admin").first()

    for user in users:
        user_matches = Match.query.filter_by(user_id=user.id)
        user.number_score_guess = 0
        user.number_match_guess = 0
        user.points = 0

        for match in user_matches:
            admin_match = Match.query.filter_by(
                user_id=admin.id, team1=match.team1, team2=match.team2
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
