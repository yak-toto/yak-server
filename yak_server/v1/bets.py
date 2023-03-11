import logging
from http import HTTPStatus
from itertools import chain
from operator import attrgetter
from time import sleep
from uuid import uuid4

from flask import Blueprint, current_app, request
from sqlalchemy import and_

from yak_server import db
from yak_server.database.models import (
    BinaryBetModel,
    GroupModel,
    GroupPositionModel,
    MatchModel,
    PhaseModel,
    ScoreBetModel,
    is_locked,
    is_phase_locked,
)
from yak_server.database.query import bets_from_group_code, bets_from_phase_code
from yak_server.helpers.group_position import update_group_position
from yak_server.helpers.logging import (
    group_position_lock_retry,
    modify_binary_bet_successfully,
    modify_score_bet_successfully,
)

from .utils.auth_utils import token_required
from .utils.constants import GLOBAL_ENDPOINT, VERSION
from .utils.errors import (
    BetNotFound,
    GroupNotFound,
    LockedBets,
    NewScoreNegative,
    PhaseNotFound,
    WrongInputs,
)
from .utils.flask_utils import success_response

bets = Blueprint("bets", __name__)

logger = logging.getLogger(__name__)


@bets.put(f"/{GLOBAL_ENDPOINT}/{VERSION}/bets/phases/<string:phase_code>")
@token_required
def create_bet(current_user, phase_code):
    phase = PhaseModel.query.filter_by(code=phase_code).first()

    if is_phase_locked(phase.code, current_user.name):
        raise LockedBets

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

    existing_score_bets = (
        current_user.score_bets.filter(MatchModel.group_id.in_(map(attrgetter("id"), groups)))
        .join(ScoreBetModel.match)
        .join(MatchModel.group)
        .order_by(GroupModel.index, MatchModel.index)
    )

    body = request.get_json()

    new_matches = []
    new_binary_bets = []
    new_score_bets = []

    for bet in body:
        if (
            not bet.get("group", {}).get("id")
            or not bet.get("team1", {}).get("id")
            or not bet.get("team2", {}).get("id")
            or not bet.get("index")
        ):
            raise WrongInputs

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

        if "is_one_won" in bet:
            binary_bet = BinaryBetModel.query.filter_by(
                match_id=match.id,
                user_id=current_user.id,
            ).first()

            if not binary_bet:
                binary_bet = BinaryBetModel(match_id=match.id, user_id=current_user.id)

            binary_bet.is_one_won = bet["is_one_won"]

            new_binary_bets.append(binary_bet)

        elif (
            "team1" in bet
            and "team2" in bet
            and "score" in bet.get("team1", {})
            and "score" in bet.get("team2", {})
        ):
            score_bet = ScoreBetModel.query.filter_by(
                match_id=match.id,
                user_id=current_user.id,
            ).first()

            if not score_bet:
                score_bet = ScoreBetModel(match_id=match.id, user_id=current_user.id)

            score_bet.score1 = bet["team1"]["score1"]
            score_bet.score2 = bet["team1"]["score2"]

            new_score_bets.append(score_bet)

        else:
            raise WrongInputs

    db.session.add_all(new_matches)
    db.session.commit()

    db.session.add_all(new_score_bets)
    db.session.commit()

    for bet in existing_score_bets:
        if bet.id not in map(attrgetter("id"), new_score_bets):
            db.session.delete(bet)

    db.session.add_all(new_binary_bets)
    db.session.commit()

    for bet in existing_binary_bets:
        if bet.id not in map(attrgetter("id"), new_binary_bets):
            db.session.delete(bet)

    db.session.commit()

    phase, groups, score_bets, binary_bets = bets_from_phase_code(
        current_user,
        phase_code,
    )

    return success_response(
        HTTPStatus.OK,
        {
            "phase": phase.to_dict(),
            "groups": [group.to_dict_without_phase() for group in groups],
            "score_bets": [score_bet.to_dict_with_group_id() for score_bet in score_bets],
            "binary_bets": [binary_bet.to_dict_with_group_id() for binary_bet in binary_bets],
        },
    )


@bets.get(f"/{GLOBAL_ENDPOINT}/{VERSION}/bets")
@token_required
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
@token_required
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
@token_required
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
@token_required
def group_result_get(current_user, group_code):
    return success_response(
        HTTPStatus.OK,
        get_group_rank_with_code(current_user.id, group_code),
    )


def get_group_rank_with_code(user_id, group_code):
    group = GroupModel.query.filter_by(code=group_code).first()

    group_rank = GroupPositionModel.query.filter_by(group_id=group.id, user_id=user_id)

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


@bets.patch(f"/{GLOBAL_ENDPOINT}/{VERSION}/score_bets/<string:bet_id>")
@token_required
def modify_score_bet(user, bet_id):
    body = request.get_json()

    if "score" not in body["team1"] or "score" not in body["team2"]:
        raise WrongInputs

    score_bet = ScoreBetModel.query.filter_by(user_id=user.id, id=bet_id).first()

    if not score_bet:
        raise BetNotFound(bet_id)

    if is_locked(score_bet):
        raise LockedBets

    if score_bet.score1 != body["team1"]["score"] or score_bet.score2 != body["team2"]["score"]:
        if (body["team1"]["score"] is not None and body["team1"]["score"] < 0) or (
            body["team2"]["score"] is not None and body["team2"]["score"] < 0
        ):
            raise NewScoreNegative

        retry_time = 0.1
        number_of_retries = 5

        for i in range(number_of_retries):
            try:
                group_position_team1 = (
                    GroupPositionModel.query.filter_by(
                        team_id=score_bet.match.team1_id,
                        user_id=user.id,
                    )
                    .with_for_update()
                    .first()
                )
                break
            except Exception:
                logger.info(
                    group_position_lock_retry(
                        score_bet.match.team1.description,
                        score_bet.match.team2.description,
                        retry_time,
                        i + 1,
                    ),
                )
                sleep(retry_time)

        for i in range(number_of_retries):
            try:
                group_position_team2 = (
                    GroupPositionModel.query.filter_by(
                        team_id=score_bet.match.team2_id,
                        user_id=user.id,
                    )
                    .with_for_update()
                    .first()
                )
                break
            except Exception:
                logger.info(
                    group_position_lock_retry(
                        score_bet.match.team1.description,
                        score_bet.match.team2.description,
                        retry_time,
                        i + 1,
                    ),
                )
                sleep(retry_time)

        update_group_position(
            score_bet.score1,
            score_bet.score2,
            body["team1"]["score"],
            body["team2"]["score"],
            group_position_team1,
            group_position_team2,
        )

        logger.info(
            modify_score_bet_successfully(
                user.name,
                score_bet,
                body["team1"]["score"],
                body["team2"]["score"],
            ),
        )

        score_bet.score1 = body["team1"]["score"]
        score_bet.score2 = body["team2"]["score"]
        db.session.commit()

    return success_response(
        HTTPStatus.OK,
        {
            "phase": score_bet.match.group.phase.to_dict(),
            "group": score_bet.match.group.to_dict_without_phase(),
            "score_bet": score_bet.to_dict_without_group(),
        },
    )


@bets.patch(f"/{GLOBAL_ENDPOINT}/{VERSION}/binary_bets/<string:bet_id>")
@token_required
def modify_binary_bet(user, bet_id):
    body = request.get_json()

    if "is_one_won" not in body:
        raise WrongInputs

    binary_bet = BinaryBetModel.query.filter_by(user_id=user.id, id=bet_id).first()

    if not binary_bet:
        raise BetNotFound(bet_id)

    if is_locked(binary_bet):
        raise LockedBets

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


@bets.get(f"/{GLOBAL_ENDPOINT}/{VERSION}/score_bets/<string:bet_id>")
@token_required
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
@token_required
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
@token_required
def commit_finale_phase(current_user):
    finale_phase_config = current_app.config["FINALE_PHASE_CONFIG"]

    groups_result = {
        group.code: get_group_rank_with_code(current_user.id, group.code)["group_rank"]
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
