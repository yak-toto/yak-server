import json
from typing import Tuple

from flask import Blueprint
from flask import jsonify
from flask import render_template
from flask import request
from flask_login import current_user
from flask_login import login_required
from sqlalchemy import select

from . import db
from .models import Match
from .models import User
from .telegram_sender import send_message

main = Blueprint("main", __name__)

with open("server/matches.json") as file:
    matches = json.load(file)
    GROUPS = tuple(matches.keys())


@main.route("/")
def index():
    return render_template("index.html")


@main.route("/profile")
@login_required
def profile():
    return render_template("profile.html", name=current_user.name, groups=GROUPS)


@main.route("/groups/<group_name>")
def groups(group_name):
    if group_name not in GROUPS:
        return "bad request!", 404

    query = select(Match.team1, Match.score1, Match.score2, Match.team2).filter_by(
        name=current_user.name, group_name=group_name
    )
    matches_resource = list(db.session.execute(query))

    return jsonify(
        [
            [
                {"team": match[0], "score": match[1]},
                {"score": match[2], "team": match[3]},
            ]
            for match in matches_resource
        ]
    )


@main.route("/groups/<group_name>", methods=["POST"])
def group_post(group_name):
    if group_name not in GROUPS:
        return "bad request!", 404

    score_first_column = request.form.getlist("score_first_column[]")
    score_second_column = request.form.getlist("score_second_column[]")

    # if string not empty, convert to int, else None
    score_first_column = [int(score) if score else None for score in score_first_column]
    score_second_column = [
        int(score) if score else None for score in score_second_column
    ]

    matches = Match.query.filter_by(name=current_user.name, group_name=group_name)

    is_matches_modified = False
    for index, match in enumerate(matches):
        if (
            match.score1 != score_first_column[index]
            or match.score2 != score_second_column[index]
        ):
            is_matches_modified = True
            match.score1 = score_first_column[index]
            match.score2 = score_second_column[index]
            send_message(
                f"User {current_user.name} update match {match.team1} - "
                f"{match.team2} with the score {match.score1} - {match.score2}."
            )
            db.session.add(match)

    db.session.commit()

    if current_user.name == "admin" and is_matches_modified:
        compute_points()

    return render_template(
        "groups.html", group_name=group_name, groups=GROUPS, matches=matches
    )


@main.route("/groups/names")
def groups_names():
    return jsonify(GROUPS), 200


@main.route("/score_board")
def score_board():
    query = (
        select(User.name, User.points)
        .order_by(User.points.desc())
        .filter(User.name != "admin")
    )
    score_board_resource = list(db.session.execute(query))

    return render_template(
        "score_board.html", groups=GROUPS, score_board_resource=score_board_resource
    )


def compute_points():
    users = User.query.filter(User.name != "admin")

    for user in users:
        points = 0
        user_matches = Match.query.filter_by(name=user.name)

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
