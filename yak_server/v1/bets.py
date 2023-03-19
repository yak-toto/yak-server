import logging
from http import HTTPStatus
from itertools import chain
from operator import attrgetter
from uuid import uuid4

from flask import Blueprint, current_app, request
from sqlalchemy import and_, update
from sqlalchemy.exc import IntegrityError

from yak_server import db
from yak_server.database.models import (
    BinaryBetModel,
    GroupModel,
    GroupPositionModel,
    MatchModel,
    PhaseModel,
    ScoreBetModel,
    is_locked,
)
from yak_server.database.query import (
    bets_from_group_code,
    bets_from_phase_code,
    binary_bets_from_phase_code,
)
from yak_server.helpers.group_position import compute_group_rank
from yak_server.helpers.logging import (
    modify_binary_bet_successfully,
    modify_score_bet_successfully,
)

from .utils.auth_utils import is_authentificated
from .utils.constants import GLOBAL_ENDPOINT, VERSION
from .utils.errors import (
    BetNotFound,
    GroupNotFound,
    LockedBets,
    PhaseNotFound,
    TeamNotFound,
)
from .utils.flask_utils import success_response
from .utils.schemas import (
    SCHEMA_PATCH_BINARY_BET,
    SCHEMA_PATCH_SCORE_BET,
    SCHEMA_POST_BINARY_BET,
    SCHEMA_POST_SCORE_BET,
    SCHEMA_PUT_BINARY_BETS_BY_PHASE,
)
from .utils.validation import validate_body

bets = Blueprint("bets", __name__)

logger = logging.getLogger(__name__)


@bets.put(f"/{GLOBAL_ENDPOINT}/{VERSION}/binary_bets/phases/<string:phase_code>")
@validate_body(schema=SCHEMA_PUT_BINARY_BETS_BY_PHASE)
@is_authentificated
def create_bet(current_user, phase_code):
    if is_locked(current_user.name):
        raise LockedBets

    phase = PhaseModel.query.filter_by(code=phase_code).first()

    finale_phase_config = current_app.config["FINALE_PHASE_CONFIG"]

    groups = GroupModel.query.filter(
        and_(
            GroupModel.phase_id == phase.id,
            GroupModel.code != finale_phase_config["first_group"],
        ),
    )

    existing_binary_bets = (
        current_user.binary_bets.filter(
            MatchModel.group_id.in_(map(attrgetter("id"), groups)),
        )
        .join(BinaryBetModel.match)
        .join(MatchModel.group)
        .order_by(GroupModel.index, MatchModel.index)
    )

    body = request.get_json()

    new_matches = []
    new_binary_bets = []

    for bet in body:
        group_id = bet["group"]["id"]
        team1_id = bet["team1"]["id"]
        team2_id = bet["team2"]["id"]
        index = bet["index"]

        match = MatchModel.query.filter_by(
            group_id=group_id,
            index=index,
            team1_id=team1_id,
            team2_id=team2_id,
        ).first()

        if not match:
            match = MatchModel(
                id=str(uuid4()),
                group_id=group_id,
                index=index,
                team1_id=team1_id,
                team2_id=team2_id,
            )

        new_matches.append(match)

        binary_bet = BinaryBetModel.query.filter_by(
            match_id=match.id,
            user_id=current_user.id,
        ).first()

        if not binary_bet:
            binary_bet = BinaryBetModel(match_id=match.id, user_id=current_user.id)

        binary_bet.is_one_won = bet["is_one_won"]

        new_binary_bets.append(binary_bet)

    db.session.add_all(new_matches)
    db.session.commit()

    db.session.add_all(new_binary_bets)
    db.session.commit()

    for bet in existing_binary_bets:
        if bet.id not in map(attrgetter("id"), new_binary_bets):
            db.session.delete(bet)

    db.session.commit()

    phase, groups, binary_bets = binary_bets_from_phase_code(
        current_user,
        phase_code,
    )

    return success_response(
        HTTPStatus.OK,
        {
            "phase": phase.to_dict(),
            "groups": [group.to_dict_without_phase() for group in groups],
            "binary_bets": [binary_bet.to_dict_with_group_id() for binary_bet in binary_bets],
        },
    )


@bets.get(f"/{GLOBAL_ENDPOINT}/{VERSION}/bets")
@is_authentificated
def get_all_bets(current_user):
    binary_bets_query = (
        current_user.binary_bets.join(BinaryBetModel.match)
        .join(MatchModel.group)
        .order_by(GroupModel.index, MatchModel.index)
    )

    score_bets_query = (
        current_user.score_bets.join(ScoreBetModel.match)
        .join(MatchModel.group)
        .order_by(GroupModel.index, MatchModel.index)
    )

    group_query = GroupModel.query.order_by(GroupModel.index)

    phase_query = PhaseModel.query.order_by(PhaseModel.index)

    return success_response(
        HTTPStatus.OK,
        {
            "phases": [phase.to_dict() for phase in phase_query],
            "groups": [group.to_dict_with_phase_id() for group in group_query],
            "score_bets": [score_bet.to_dict_with_group_id() for score_bet in score_bets_query],
            "binary_bets": [binary_bet.to_dict_with_group_id() for binary_bet in binary_bets_query],
        },
    )


@bets.get(f"/{GLOBAL_ENDPOINT}/{VERSION}/bets/phases/<string:phase_code>")
@is_authentificated
def get_bets_by_phase(current_user, phase_code):
    phase, groups, score_bets, binary_bets = bets_from_phase_code(
        current_user,
        phase_code,
    )

    if not phase:
        raise PhaseNotFound(phase_code)

    return success_response(
        HTTPStatus.OK,
        {
            "phase": phase.to_dict(),
            "groups": [group.to_dict_without_phase() for group in groups],
            "score_bets": [score_bet.to_dict_with_group_id() for score_bet in score_bets],
            "binary_bets": [binary_bet.to_dict_with_group_id() for binary_bet in binary_bets],
        },
    )


@bets.get(f"/{GLOBAL_ENDPOINT}/{VERSION}/bets/groups/<string:group_code>")
@is_authentificated
def group_get(current_user, group_code):
    group, score_bets, binary_bets = bets_from_group_code(current_user, group_code)

    if not group:
        raise GroupNotFound(group_code)

    return success_response(
        HTTPStatus.OK,
        {
            "phase": group.phase.to_dict(),
            "group": group.to_dict_without_phase(),
            "binary_bets": [bet.to_dict_without_group() for bet in binary_bets],
            "score_bets": [bet.to_dict_without_group() for bet in score_bets],
        },
    )


@bets.get(f"/{GLOBAL_ENDPOINT}/{VERSION}/bets/groups/rank/<string:group_code>")
@is_authentificated
def group_result_get(current_user, group_code):
    return success_response(
        HTTPStatus.OK,
        get_group_rank_with_code(current_user, group_code),
    )


def get_group_rank_with_code(user, group_code):
    group = GroupModel.query.filter_by(code=group_code).first()

    if not group:
        raise GroupNotFound(group_code)

    group_rank = GroupPositionModel.query.filter_by(group_id=group.id, user_id=user.id)

    def send_response(group, group_rank):
        return {
            "phase": group.phase.to_dict(),
            "group": group.to_dict_without_phase(),
            "group_rank": sorted(
                [group_position.to_dict() for group_position in group_rank],
                key=lambda team: (
                    team["points"],
                    team["goals_difference"],
                    team["goals_for"],
                ),
                reverse=True,
            ),
        }

    if not any(group_position.need_recomputation for group_position in group_rank):
        return send_response(group, group_rank)

    score_bets = user.score_bets.filter(MatchModel.group_id == group.id).join(ScoreBetModel.match)

    group_rank = compute_group_rank(group_rank, score_bets)

    db.session.commit()

    return send_response(group, group_rank)


@bets.post(f"/{GLOBAL_ENDPOINT}/{VERSION}/score_bets")
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


@bets.patch(f"/{GLOBAL_ENDPOINT}/{VERSION}/score_bets/<string:bet_id>")
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


@bets.delete(f"/{GLOBAL_ENDPOINT}/{VERSION}/score_bets/<string:bet_id>")
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


@bets.post(f"/{GLOBAL_ENDPOINT}/{VERSION}/binary_bets")
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


@bets.patch(f"/{GLOBAL_ENDPOINT}/{VERSION}/binary_bets/<string:bet_id>")
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


@bets.delete(f"/{GLOBAL_ENDPOINT}/{VERSION}/binary_bets/<string:bet_id>")
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


@bets.get(f"/{GLOBAL_ENDPOINT}/{VERSION}/score_bets/<string:bet_id>")
@is_authentificated
def retrieve_score_bet_by_id(user, bet_id):
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


@bets.get(f"/{GLOBAL_ENDPOINT}/{VERSION}/binary_bets/<string:bet_id>")
@is_authentificated
def retrieve_binary_bet_by_id(user, bet_id):
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


@bets.post(f"/{GLOBAL_ENDPOINT}/{VERSION}/bets/finale_phase")
@is_authentificated
def commit_finale_phase(current_user):
    finale_phase_config = current_app.config["FINALE_PHASE_CONFIG"]

    groups_result = {
        group.code: get_group_rank_with_code(current_user, group.code)["group_rank"]
        for group in GroupModel.query.join(GroupModel.phase).filter(
            PhaseModel.code == "GROUP",
        )
    }

    first_phase_phase_group = GroupModel.query.filter_by(
        code=finale_phase_config["first_group"],
    ).first()

    existing_binary_bets = BinaryBetModel.query.join(BinaryBetModel.match).filter(
        and_(
            BinaryBetModel.user_id == current_user.id,
            MatchModel.group_id == first_phase_phase_group.id,
        ),
    )

    existing_matches = map(attrgetter("match"), existing_binary_bets)

    new_binary_bets = []
    new_matches = []

    for index, match_config in enumerate(finale_phase_config["versus"], 1):
        if all(
            team["played"] == len(groups_result[match_config["team1"]["group"]]) - 1
            for team in chain(
                groups_result[match_config["team1"]["group"]],
                groups_result[match_config["team2"]["group"]],
            )
        ):
            team1 = groups_result[match_config["team1"]["group"]][
                match_config["team1"]["rank"] - 1
            ]["team"]
            team2 = groups_result[match_config["team2"]["group"]][
                match_config["team2"]["rank"] - 1
            ]["team"]

            match = MatchModel.query.filter_by(
                group_id=first_phase_phase_group.id,
                team1_id=team1["id"],
                team2_id=team2["id"],
                index=index,
            ).first()

            if not match:
                match = MatchModel(
                    id=str(uuid4()),
                    group_id=first_phase_phase_group.id,
                    team1_id=team1["id"],
                    team2_id=team2["id"],
                    index=index,
                )

            new_matches.append(match)

            bet = BinaryBetModel.query.filter_by(
                user_id=current_user.id,
                match_id=match.id,
            ).first()

            if not bet:
                bet = BinaryBetModel(
                    user_id=current_user.id,
                    match_id=match.id,
                )

            new_binary_bets.append(bet)

    # Compare existing matches/bets and new matches/bets
    db.session.add_all(new_matches)
    db.session.commit()

    db.session.add_all(new_binary_bets)
    db.session.commit()

    is_bet_modified = False

    for bet in existing_binary_bets:
        if bet.id not in map(attrgetter("id"), new_binary_bets):
            is_bet_modified = True
            db.session.delete(bet)

    db.session.commit()

    for match in existing_matches:
        if match.id not in map(attrgetter("id"), new_matches) and not match.binary_bets:
            db.session.delete(match)

    db.session.commit()

    if is_bet_modified:
        for bet in BinaryBetModel.query.filter_by(user_id=current_user.id):
            if bet.match.group.code in GroupModel.query.join(GroupModel.phase).filter(
                and_(
                    PhaseModel.code == "FINAL",
                    GroupModel.id == first_phase_phase_group.id,
                ),
            ):
                db.session.delete(bet)
        db.session.commit()

    phase, groups, score_bets, binary_bets = bets_from_phase_code(current_user, "FINAL")

    return success_response(
        HTTPStatus.OK,
        {
            "phase": phase.to_dict(),
            "groups": [group.to_dict_without_phase() for group in groups],
            "score_bets": [score_bet.to_dict_with_group_id() for score_bet in score_bets],
            "binary_bets": [binary_bet.to_dict_with_group_id() for binary_bet in binary_bets],
        },
    )
