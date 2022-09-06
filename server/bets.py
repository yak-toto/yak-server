from itertools import chain

from flask import Blueprint
from flask import request
from sqlalchemy import and_

from . import db
from .models import Bet
from .models import BinaryBet
from .models import Group
from .models import is_locked
from .models import Match
from .utils.auth_utils import token_required
from .utils.constants import BINARY
from .utils.constants import GLOBAL_ENDPOINT
from .utils.constants import SCORE
from .utils.constants import VERSION
from .utils.errors import invalid_bet_type
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
            (
                score.to_dict()
                for score in chain(current_user.bets, current_user.binary_bets)
            ),
            key=lambda score: (score["group"]["code"], score["index"]),
        ),
    )


@bets.route(f"/{GLOBAL_ENDPOINT}/{VERSION}/bets/groups/<string:group_code>")
@token_required
def group_get(current_user, group_code):
    group = Group.query.filter_by(code=group_code).first()

    matches = Match.query.filter_by(group_id=group.id)

    bets = Bet.query.filter(
        and_(
            Bet.user_id == current_user.id,
            Bet.match_id.in_(match.id for match in matches),
        )
    )

    binary_bets = BinaryBet.query.filter(
        and_(
            BinaryBet.user_id == current_user.id,
            BinaryBet.match_id.in_(match.id for match in matches),
        )
    )

    return success_response(
        200,
        sorted(
            (score.to_dict() for score in chain(bets, binary_bets)),
            key=lambda score: score["index"],
        ),
    )


@bets.route(
    f"/{GLOBAL_ENDPOINT}/{VERSION}/bets/scores/<string:match_id>",
    methods=["PATCH"],
)
@token_required
def match_patch(current_user, match_id):
    body = request.get_json()

    bet_type = request.args.get("type")

    if bet_type == SCORE:
        bet = Bet.query.filter_by(user_id=current_user.id, match_id=match_id).first()

        if "score" not in body["team1"] and "score" not in body["team2"]:
            return failed_response(*wrong_inputs)

    elif bet_type == BINARY:
        bet = BinaryBet.query.filter_by(
            user_id=current_user.id, match_id=match_id
        ).first()

        if "is_one_won" not in body:
            return failed_response(*wrong_inputs)

    else:
        return failed_response(*invalid_bet_type)

    if not bet:
        return failed_response(*match_not_found)

    if bet_type == "score":
        if is_locked(bet):
            return failed_response(*locked_bets)

        if bet.score1 != body["team1"].get("score") or bet.score2 != body["team2"].get(
            "score"
        ):
            bet.score1 = body["team1"].get("score")
            bet.score2 = body["team2"].get("score")
            db.session.commit()

            log_score_bet(
                current_user.name,
                bet.match.team1,
                bet.match.team2,
                bet.score1,
                bet.score2,
            )

    else:
        if is_locked(bet):
            return failed_response(*locked_bets)

        if bet.is_one_won != body["is_one_won"]:
            bet.is_one_won = body["is_one_won"]
            db.session.commit()

            log_binary_bet(
                current_user.name,
                bet.match.team1.description,
                bet.match.team2.description,
                bet.is_one_won,
            )

    return success_response(200, bet.to_dict())


def log_score_bet(user_name, team1, team2, score1, score2):
    send_message(
        f"User {user_name} update match {team1} - "
        f"{team2} with the score {score1} - {score2}."
    )


def log_binary_bet(user_name, team1, team2, is_one_won):
    send_message(
        f"User {user_name} update match with victory of "
        f"{team1 if is_one_won else team2} "
        f"against {team2 if is_one_won else team1}."
    )


@bets.route(f"/{GLOBAL_ENDPOINT}/{VERSION}/bets/scores/<string:match_id>")
@token_required
def bet_get(current_user, match_id):
    bet_type = request.args.get("type")

    if bet_type == "score":
        bet = Bet.query.filter_by(user_id=current_user.id, match_id=match_id).first()
    elif bet_type == "binary":
        bet = BinaryBet.query.filter_by(
            user_id=current_user.id, match_id=match_id
        ).first()
    else:
        return failed_response(*invalid_bet_type)

    if not bet:
        return failed_response(*match_not_found)

    return success_response(200, bet.to_dict())
