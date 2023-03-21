import logging
from http import HTTPStatus

from flask import Blueprint, request
from sqlalchemy import update
from sqlalchemy.exc import IntegrityError

from yak_server import db
from yak_server.database.models import (
    GroupPositionModel,
    MatchModel,
    ScoreBetModel,
    is_locked,
)
from yak_server.helpers.logging import modify_score_bet_successfully

from .utils.auth_utils import is_authentificated
from .utils.constants import GLOBAL_ENDPOINT, VERSION
from .utils.errors import (
    BetNotFound,
    GroupNotFound,
    LockedBets,
    TeamNotFound,
)
from .utils.flask_utils import success_response
from .utils.schemas import SCHEMA_PATCH_SCORE_BET, SCHEMA_POST_SCORE_BET
from .utils.validation import validate_body

score_bets = Blueprint("score_bets", __name__)

logger = logging.getLogger(__name__)


@score_bets.post(f"/{GLOBAL_ENDPOINT}/{VERSION}/score_bets")
@validate_body(schema=SCHEMA_POST_SCORE_BET)
@is_authentificated
def create_score_bet(user):
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

    score_bet = ScoreBetModel(
        match_id=match.id,
        user_id=user.id,
        score1=body["team1"].get("score"),
        score2=body["team2"].get("score"),
    )

    db.session.execute(
        update(GroupPositionModel)
        .values(need_recomputation=True)
        .where(
            GroupPositionModel.team_id == body["team1"]["id"],
            GroupPositionModel.user_id == user.id,
        ),
    )
    db.session.execute(
        update(GroupPositionModel)
        .values(need_recomputation=True)
        .where(
            GroupPositionModel.team_id == body["team2"]["id"],
            GroupPositionModel.user_id == user.id,
        ),
    )

    db.session.add(score_bet)
    db.session.commit()

    return success_response(
        HTTPStatus.CREATED,
        {
            "phase": score_bet.match.group.phase.to_dict(),
            "group": score_bet.match.group.to_dict_without_phase(),
            "score_bet": score_bet.to_dict_without_group(),
        },
    )


@score_bets.get(f"/{GLOBAL_ENDPOINT}/{VERSION}/score_bets/<string:bet_id>")
@is_authentificated
def retrieve_score_bet(user, bet_id):
    score_bet = ScoreBetModel.query.filter_by(user_id=user.id, id=bet_id).first()

    if not score_bet:
        raise BetNotFound(bet_id)

    return success_response(
        HTTPStatus.OK,
        {
            "phase": score_bet.match.group.phase.to_dict(),
            "group": score_bet.match.group.to_dict_without_phase(),
            "score_bet": score_bet.to_dict_without_group(),
        },
    )


@score_bets.patch(f"/{GLOBAL_ENDPOINT}/{VERSION}/score_bets/<string:bet_id>")
@validate_body(schema=SCHEMA_PATCH_SCORE_BET)
@is_authentificated
def modify_score_bet(user, bet_id):
    if is_locked(user.name):
        raise LockedBets

    score_bet = ScoreBetModel.query.filter_by(user_id=user.id, id=bet_id).with_for_update().first()

    if not score_bet:
        raise BetNotFound(bet_id)

    def send_response(score_bet):
        return success_response(
            HTTPStatus.OK,
            {
                "phase": score_bet.match.group.phase.to_dict(),
                "group": score_bet.match.group.to_dict_without_phase(),
                "score_bet": score_bet.to_dict_without_group(),
            },
        )

    body = request.get_json()

    if score_bet.score1 == body["team1"]["score"] and score_bet.score2 == body["team2"]["score"]:
        return send_response(score_bet)

    logger.info(
        modify_score_bet_successfully(
            user.name,
            score_bet,
            body["team1"]["score"],
            body["team2"]["score"],
        ),
    )

    db.session.execute(
        update(GroupPositionModel)
        .values(need_recomputation=True)
        .where(
            GroupPositionModel.team_id == score_bet.match.team1_id,
            GroupPositionModel.user_id == user.id,
        ),
    )
    db.session.execute(
        update(GroupPositionModel)
        .values(need_recomputation=True)
        .where(
            GroupPositionModel.team_id == score_bet.match.team2_id,
            GroupPositionModel.user_id == user.id,
        ),
    )

    score_bet.score1 = body["team1"]["score"]
    score_bet.score2 = body["team2"]["score"]
    db.session.commit()

    return send_response(score_bet)


@score_bets.delete(f"/{GLOBAL_ENDPOINT}/{VERSION}/score_bets/<string:bet_id>")
@is_authentificated
def delete_score_bet(user, bet_id):
    if is_locked(user.name):
        raise LockedBets

    score_bet = ScoreBetModel.query.filter_by(id=bet_id, user_id=user.id).first()

    if not score_bet:
        raise BetNotFound(bet_id)

    response_body = {
        "phase": score_bet.match.group.phase.to_dict(),
        "group": score_bet.match.group.to_dict_without_phase(),
        "score_bet": score_bet.to_dict_without_group(),
    }

    db.session.execute(
        update(GroupPositionModel)
        .values(need_recomputation=True)
        .where(
            GroupPositionModel.team_id == score_bet.match.team1_id,
            GroupPositionModel.user_id == user.id,
        ),
    )
    db.session.execute(
        update(GroupPositionModel)
        .values(need_recomputation=True)
        .where(
            GroupPositionModel.team_id == score_bet.match.team2_id,
            GroupPositionModel.user_id == user.id,
        ),
    )

    db.session.delete(score_bet)
    db.session.commit()

    return success_response(HTTPStatus.OK, response_body)
