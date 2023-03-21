import logging
from http import HTTPStatus

from flask import Blueprint, request
from sqlalchemy.exc import IntegrityError

from yak_server import db
from yak_server.database.models import (
    BinaryBetModel,
    MatchModel,
    is_locked,
)
from yak_server.helpers.logging import modify_binary_bet_successfully

from .utils.auth_utils import is_authentificated
from .utils.constants import GLOBAL_ENDPOINT, VERSION
from .utils.errors import (
    BetNotFound,
    GroupNotFound,
    LockedBets,
    TeamNotFound,
)
from .utils.flask_utils import success_response
from .utils.schemas import SCHEMA_PATCH_BINARY_BET, SCHEMA_POST_BINARY_BET
from .utils.validation import validate_body

binary_bets = Blueprint("binary_bets", __name__)

logger = logging.getLogger(__name__)


@binary_bets.post(f"/{GLOBAL_ENDPOINT}/{VERSION}/binary_bets")
@validate_body(schema=SCHEMA_POST_BINARY_BET)
@is_authentificated
def create_binary_bet(user):
    if is_locked(user.name):
        raise LockedBets

    body = request.get_json()

    match = MatchModel(
        team1_id=body["team1"]["id"],
        team2_id=body["team2"]["id"],
        index=body["index"],
        group_id=body["group"]["id"],
    )

    db.session.add(match)

    try:
        db.session.flush()
    except IntegrityError as integrity_error:
        if "FOREIGN KEY (`team1_id`)" in str(integrity_error):
            raise TeamNotFound(team_id=body["team1"]["id"]) from integrity_error
        elif "FOREIGN KEY (`team2_id`)" in str(integrity_error):
            raise TeamNotFound(team_id=body["team2"]["id"]) from integrity_error
        else:
            raise GroupNotFound(group_id=body["group"]["id"]) from integrity_error

    binary_bet = BinaryBetModel(
        match_id=match.id,
        user_id=user.id,
        is_one_won=body.get("is_one_won"),
    )

    db.session.add(binary_bet)
    db.session.commit()

    return success_response(
        HTTPStatus.CREATED,
        {
            "phase": binary_bet.match.group.phase.to_dict(),
            "group": binary_bet.match.group.to_dict_without_phase(),
            "binary_bet": binary_bet.to_dict_without_group(),
        },
    )


@binary_bets.get(f"/{GLOBAL_ENDPOINT}/{VERSION}/binary_bets/<string:bet_id>")
@is_authentificated
def retrieve_binary_bet(user, bet_id):
    binary_bet = BinaryBetModel.query.filter_by(user_id=user.id, id=bet_id).first()

    if not binary_bet:
        raise BetNotFound(bet_id)

    return success_response(
        HTTPStatus.OK,
        {
            "phase": binary_bet.match.group.phase.to_dict(),
            "group": binary_bet.match.group.to_dict_without_phase(),
            "binary_bet": binary_bet.to_dict_without_group(),
        },
    )


@binary_bets.patch(f"/{GLOBAL_ENDPOINT}/{VERSION}/binary_bets/<string:bet_id>")
@validate_body(schema=SCHEMA_PATCH_BINARY_BET)
@is_authentificated
def modify_binary_bet(user, bet_id):
    if is_locked(user.name):
        raise LockedBets

    binary_bet = BinaryBetModel.query.filter_by(user_id=user.id, id=bet_id).first()

    if not binary_bet:
        raise BetNotFound(bet_id)

    body = request.get_json()

    logger.info(modify_binary_bet_successfully(user.name, binary_bet, body["is_one_won"]))

    binary_bet.is_one_won = body["is_one_won"]
    db.session.commit()

    return success_response(
        HTTPStatus.OK,
        {
            "phase": binary_bet.match.group.phase.to_dict(),
            "group": binary_bet.match.group.to_dict_without_phase(),
            "binary_bet": binary_bet.to_dict_without_group(),
        },
    )


@binary_bets.delete(f"/{GLOBAL_ENDPOINT}/{VERSION}/binary_bets/<string:bet_id>")
@is_authentificated
def delete_binary_bet(user, bet_id):
    if is_locked(user.name):
        raise LockedBets

    binary_bet = BinaryBetModel.query.filter_by(id=bet_id, user_id=user.id).first()

    if not binary_bet:
        raise BetNotFound(bet_id)

    response_body = {
        "phase": binary_bet.match.group.phase.to_dict(),
        "group": binary_bet.match.group.to_dict_without_phase(),
        "binary_bet": binary_bet.to_dict_without_group(),
    }

    db.session.delete(binary_bet)
    db.session.commit()

    return success_response(HTTPStatus.OK, response_body)
