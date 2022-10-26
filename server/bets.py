from itertools import chain

from flask import Blueprint
from flask import request
from sqlalchemy import and_

from . import db
from .models import BinaryBet
from .models import Group
from .models import is_locked
from .models import Match
from .models import ScoreBet
from .utils.auth_utils import token_required
from .utils.constants import BINARY
from .utils.constants import GLOBAL_ENDPOINT
from .utils.constants import SCORE
from .utils.constants import VERSION
from .utils.errors import duplicated_ids
from .utils.errors import invalid_bet_type
from .utils.errors import locked_bets
from .utils.errors import match_not_found
from .utils.errors import missing_id
from .utils.errors import wrong_inputs
from .utils.flask_utils import failed_response
from .utils.flask_utils import success_response
from .utils.telegram_sender import send_message


bets = Blueprint("bets", __name__)


@bets.route(f"/{GLOBAL_ENDPOINT}/{VERSION}/bets")
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


@bets.route(f"/{GLOBAL_ENDPOINT}/{VERSION}/bets", methods=["PATCH"])
@token_required
def modify_bets(current_user):
    # Reject if any input bet does not contain id
    if not all(bet.get("id") for bet in request.get_json()):
        return failed_response(*missing_id)

    bet_ids = [bet["id"] for bet in request.get_json()]

    # Reject if there are duplicated ids in input bets
    if len(bet_ids) != len(set(bet_ids)):
        return failed_response(*duplicated_ids)

    results = []
    telegram_logs = {"score": [], "binary": []}

    for bet in request.get_json():
        # Deduce type bet from request
        if (
            "team1" in bet
            and "team2" in bet
            and "score" in bet["team1"]
            and "score" in bet["team2"]
        ):
            bet_type = SCORE
            original_bet = ScoreBet.query.filter_by(
                match_id=bet["id"], user_id=current_user.id
            ).first()
        elif "is_one_won" in bet:
            bet_type = BINARY
            original_bet = BinaryBet.query.filter_by(
                match_id=bet["id"], user_id=current_user.id
            ).first()
        else:
            return failed_response(*wrong_inputs)

        # No bet has been found
        if not original_bet:
            return failed_response(*match_not_found)

        # Return error if bet is locked
        if is_locked(original_bet):
            return failed_response(*locked_bets)

        # Modify bet depending on their type if the bet has been changed
        if bet_type == SCORE and (original_bet.score1, original_bet.score2) != (
            bet["team1"]["score"],
            bet["team2"]["score"],
        ):
            original_bet.score1 = bet["team1"]["score"]
            original_bet.score2 = bet["team2"]["score"]

            telegram_logs["score"].append(
                (
                    current_user.name,
                    original_bet.match.team1.description,
                    original_bet.match.team2.description,
                    original_bet.score1,
                    original_bet.score2,
                )
            )
        elif bet_type == BINARY and original_bet.is_one_won != bet["is_one_won"]:
            original_bet.is_one_won = bet["is_one_won"]

            telegram_logs["binary"].append(
                (
                    current_user.name,
                    original_bet.match.team1.description,
                    original_bet.match.team2.description,
                    original_bet.is_one_won,
                )
            )

        results.append(original_bet.to_dict())

    # Commit at the end to make sure all input are correct before pushing to db
    db.session.commit()

    for log in telegram_logs["score"]:
        log_score_bet(*log)

    for log in telegram_logs["binary"]:
        log_score_bet(*log)

    return success_response(200, results)


@bets.route(f"/{GLOBAL_ENDPOINT}/{VERSION}/bets/groups/<string:group_code>")
@token_required
def group_get(current_user, group_code):
    group = Group.query.filter_by(code=group_code).first()

    matches = Match.query.filter_by(group_id=group.id)

    bets = ScoreBet.query.filter(
        and_(
            ScoreBet.user_id == current_user.id,
            ScoreBet.match_id.in_(match.id for match in matches),
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
    f"/{GLOBAL_ENDPOINT}/{VERSION}/bets/<string:match_id>",
    methods=["PATCH"],
)
@token_required
def match_patch(current_user, match_id):
    body = request.get_json()

    bet_type = request.args.get("type")

    if bet_type == SCORE:
        bet = ScoreBet.query.filter_by(
            user_id=current_user.id, match_id=match_id
        ).first()

        if "score" not in body["team1"] or "score" not in body["team2"]:
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

    if is_locked(bet):
        return failed_response(*locked_bets)

    if bet_type == "score":
        if bet.score1 != body["team1"].get("score") or bet.score2 != body["team2"].get(
            "score"
        ):
            bet.score1 = body["team1"].get("score")
            bet.score2 = body["team2"].get("score")
            db.session.commit()

            log_score_bet(
                current_user.name,
                bet.match.team1.description,
                bet.match.team2.description,
                bet.score1,
                bet.score2,
            )

    else:
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


@bets.route(f"/{GLOBAL_ENDPOINT}/{VERSION}/bets/<string:match_id>")
@token_required
def bet_get(current_user, match_id):
    bet_type = request.args.get("type")

    if bet_type == "score":
        bet = ScoreBet.query.filter_by(
            user_id=current_user.id, match_id=match_id
        ).first()
    elif bet_type == "binary":
        bet = BinaryBet.query.filter_by(
            user_id=current_user.id, match_id=match_id
        ).first()
    else:
        return failed_response(*invalid_bet_type)

    if not bet:
        return failed_response(*match_not_found)

    return success_response(200, bet.to_dict())
