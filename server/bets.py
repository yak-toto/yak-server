from itertools import chain
from operator import attrgetter
from uuid import uuid4

from flask import Blueprint
from flask import current_app
from flask import request
from sqlalchemy import and_
from sqlalchemy import desc

from . import db
from .models import BinaryBet
from .models import Group
from .models import is_locked
from .models import is_phase_locked
from .models import Match
from .models import Phase
from .models import ScoreBet
from .query import bets_from_group_code
from .query import bets_from_phase_code
from .utils.auth_utils import token_required
from .utils.constants import BINARY
from .utils.constants import GLOBAL_ENDPOINT
from .utils.constants import SCORE
from .utils.constants import VERSION
from .utils.errors import BetNotFound
from .utils.errors import DuplicatedIds
from .utils.errors import InvalidBetType
from .utils.errors import LockedBets
from .utils.errors import MissingId
from .utils.errors import WrongInputs
from .utils.flask_utils import success_response
from .utils.telegram_sender import send_message


bets = Blueprint("bets", __name__)


@bets.put(f"/{GLOBAL_ENDPOINT}/{VERSION}/bets/phases/<string:phase_code>")
@token_required
def create_bet(current_user, phase_code):
    phase = Phase.query.filter_by(code=phase_code).first()

    if is_phase_locked(phase.code, current_user.name):
        raise LockedBets()

    finale_phase_config = current_app.config["FINALE_PHASE_CONFIG"]

    groups = Group.query.filter(
        and_(
            Group.phase_id == phase.id, Group.code != finale_phase_config["first_group"]
        )
    )

    existing_binary_bets = (
        current_user.binary_bets.filter(
            Match.group_id.in_(map(attrgetter("id"), groups))
        )
        .join(BinaryBet.match)
        .join(Match.group)
        .order_by(Group.code, Match.index)
    )

    existing_score_bets = (
        current_user.bets.filter(Match.group_id.in_(map(attrgetter("id"), groups)))
        .join(ScoreBet.match)
        .join(Match.group)
        .order_by(Group.code, Match.index)
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
            raise WrongInputs()

        group_id = bet["group"]["id"]
        team1_id = bet["team1"]["id"]
        team2_id = bet["team2"]["id"]
        index = bet["index"]

        match = Match.query.filter_by(
            group_id=group_id, index=index, team1_id=team1_id, team2_id=team2_id
        ).first()

        if not match:
            match = Match(
                id=str(uuid4()),
                group_id=group_id,
                index=index,
                team1_id=team1_id,
                team2_id=team2_id,
            )

        new_matches.append(match)

        if "is_one_won" in bet:
            binary_bet = BinaryBet.query.filter_by(
                match_id=match.id, user_id=current_user.id
            ).first()

            if not binary_bet:
                binary_bet = BinaryBet(match_id=match.id, user_id=current_user.id)

            binary_bet.is_one_won = bet["is_one_won"]

            new_binary_bets.append(binary_bet)

        elif (
            "team1" in bet
            and "team2" in bet
            and "score" in bet.get("team1", {})
            and "score" in bet.get("team2", {})
        ):
            score_bet = ScoreBet.query.filter_by(
                match_id=match.id, user_id=current_user.id
            ).first()

            if not score_bet:
                score_bet = ScoreBet(match_id=match.id, user_id=current_user.id)

            score_bet.score1 = bet["team1"]["score1"]
            score_bet.score2 = bet["team1"]["score2"]

            new_score_bets.append(score_bet)

        else:
            raise WrongInputs()

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
        current_user, phase_code
    )

    return success_response(
        200,
        {
            "phase": phase.to_dict(),
            "groups": [group.to_dict_without_phase() for group in groups],
            "score_bets": [
                score_bet.to_dict_with_group_id() for score_bet in score_bets
            ],
            "binary_bets": [
                binary_bet.to_dict_with_group_id() for binary_bet in binary_bets
            ],
        },
    )


@bets.get(f"/{GLOBAL_ENDPOINT}/{VERSION}/bets")
@token_required
def groups(current_user):
    binary_bets_query = (
        current_user.binary_bets.join(BinaryBet.match)
        .join(Match.group)
        .join(Group.phase)
        .order_by(desc(Phase.code), Group.code, Match.index)
    )

    score_bets_query = (
        current_user.bets.join(ScoreBet.match)
        .join(Match.group)
        .join(Group.phase)
        .order_by(desc(Phase.code), Group.code, Match.index)
    )

    group_query = Group.query.join(Group.phase).order_by(desc(Phase.code), Group.code)

    phase_query = Phase.query.order_by(desc(Phase.code))

    return success_response(
        200,
        {
            "phases": [phase.to_dict() for phase in phase_query],
            "groups": [group.to_dict_with_phase_id() for group in group_query],
            "score_bets": [
                score_bet.to_dict_with_group_id() for score_bet in score_bets_query
            ],
            "binary_bets": [
                binary_bet.to_dict_with_group_id() for binary_bet in binary_bets_query
            ],
        },
    )


@bets.get(f"/{GLOBAL_ENDPOINT}/{VERSION}/bets/phases/<string:phase_code>")
@token_required
def get_bets_by_phase(current_user, phase_code):
    phase, groups, score_bets, binary_bets = bets_from_phase_code(
        current_user, phase_code
    )

    return success_response(
        200,
        {
            "phase": phase.to_dict(),
            "groups": [group.to_dict_without_phase() for group in groups],
            "score_bets": [
                score_bet.to_dict_with_group_id() for score_bet in score_bets
            ],
            "binary_bets": [
                binary_bet.to_dict_with_group_id() for binary_bet in binary_bets
            ],
        },
    )


@bets.patch(f"/{GLOBAL_ENDPOINT}/{VERSION}/bets")
@token_required
def modify_bets(current_user):
    # Reject if any input bet does not contain id
    if not all(bet.get("id") for bet in request.get_json()):
        raise MissingId()

    bet_ids = [bet["id"] for bet in request.get_json()]

    # Reject if there are duplicated ids in input bets
    duplicated_ids = {bet_id for bet_id in bet_ids if bet_ids.count(bet_id) > 1}
    if duplicated_ids:
        raise DuplicatedIds(duplicated_ids)

    binary_bets = []
    score_bets = []
    telegram_logs = {"score": [], "binary": []}

    for bet in request.get_json():
        # Deduce bet type from request
        if (
            "team1" in bet
            and "team2" in bet
            and "score" in bet["team1"]
            and "score" in bet["team2"]
        ):
            bet_type = SCORE
            original_bet = ScoreBet.query.filter_by(
                id=bet["id"], user_id=current_user.id
            ).first()
        elif "is_one_won" in bet:
            bet_type = BINARY
            original_bet = BinaryBet.query.filter_by(
                id=bet["id"], user_id=current_user.id
            ).first()
        else:
            raise WrongInputs()

        # No bet has been found
        if not original_bet:
            raise BetNotFound(bet["id"])

        # Return error if bet is locked
        if is_locked(original_bet):
            raise LockedBets()

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

        if bet_type == SCORE:
            score_bets.append(original_bet)
        elif bet_type == BINARY:
            binary_bets.append(original_bet)

    # Commit at the end to make sure all input are correct before pushing to db
    db.session.commit()

    for log in telegram_logs["score"]:
        log_score_bet(*log)

    for log in telegram_logs["binary"]:
        log_binary_bet(*log)

    return success_response(
        200,
        {
            "phases": [
                phase.to_dict()
                for phase in {
                    bet.match.group.phase for bet in chain(score_bets, binary_bets)
                }
            ],
            "groups": [
                group.to_dict_with_phase_id()
                for group in {bet.match.group for bet in chain(score_bets, binary_bets)}
            ],
            "score_bets": [bet.to_dict_with_group_id() for bet in score_bets],
            "binary_bets": [bet.to_dict_with_group_id() for bet in binary_bets],
        },
    )


@bets.get(f"/{GLOBAL_ENDPOINT}/{VERSION}/bets/groups/<string:group_code>")
@token_required
def group_get(current_user, group_code):
    group, score_bets, binary_bets = bets_from_group_code(current_user, group_code)

    return success_response(
        200,
        {
            "phase": group.phase.to_dict(),
            "group": group.to_dict_without_phase(),
            "binary_bets": [bet.to_dict_without_group() for bet in binary_bets],
            "score_bets": [bet.to_dict_without_group() for bet in score_bets],
        },
    )


@bets.get(f"/{GLOBAL_ENDPOINT}/{VERSION}/bets/groups/results/<string:group_code>")
@token_required
def group_result_get(current_user, group_code):
    return success_response(
        200, get_result_with_group_code(current_user.id, group_code)
    )


def get_result_with_group_code(user_id, group_code):
    group = Group.query.filter_by(code=group_code).first()

    score_bets = (
        ScoreBet.query.filter_by(user_id=user_id)
        .filter(Match.group_id == group.id)
        .join(ScoreBet.match)
        .order_by(Match.index)
    )

    results = {}

    result_base = {
        "played": 0,
        "won": 0,
        "drawn": 0,
        "lost": 0,
        "goals_for": 0,
        "goals_against": 0,
        "goals_difference": 0,
        "points": 0,
    }

    for score_bet in score_bets:
        if score_bet.match.team1.id not in results:
            results[score_bet.match.team1.id] = (
                score_bet.match.team1.to_dict() | result_base
            )

        if score_bet.match.team2.id not in results:
            results[score_bet.match.team2.id] = (
                score_bet.match.team2.to_dict() | result_base
            )

        if score_bet.score1 is not None and score_bet.score2 is not None:
            results[score_bet.match.team1.id]["played"] += 1
            results[score_bet.match.team2.id]["played"] += 1

            results[score_bet.match.team1.id]["goals_for"] += score_bet.score1
            results[score_bet.match.team1.id]["goals_against"] += score_bet.score2
            results[score_bet.match.team1.id]["goals_difference"] += (
                score_bet.score1 - score_bet.score2
            )

            results[score_bet.match.team2.id]["goals_for"] += score_bet.score2
            results[score_bet.match.team2.id]["goals_against"] += score_bet.score1
            results[score_bet.match.team2.id]["goals_difference"] += (
                score_bet.score2 - score_bet.score1
            )

            if score_bet.score1 > score_bet.score2:
                results[score_bet.match.team1.id]["won"] += 1
                results[score_bet.match.team2.id]["lost"] += 1
                results[score_bet.match.team1.id]["points"] += 3
            elif score_bet.score1 < score_bet.score2:
                results[score_bet.match.team2.id]["won"] += 1
                results[score_bet.match.team1.id]["lost"] += 1
                results[score_bet.match.team2.id]["points"] += 3
            else:
                results[score_bet.match.team1.id]["drawn"] += 1
                results[score_bet.match.team2.id]["drawn"] += 1
                results[score_bet.match.team1.id]["points"] += 1
                results[score_bet.match.team2.id]["points"] += 1

    return {
        "phase": group.phase.to_dict(),
        "group": group.to_dict_without_phase(),
        "results": sorted(
            results.values(),
            key=lambda team: (
                team["points"],
                team["goals_difference"],
                team["goals_for"],
            ),
            reverse=True,
        ),
    }


@bets.patch(f"/{GLOBAL_ENDPOINT}/{VERSION}/bets/<string:bet_id>")
@token_required
def match_patch(current_user, bet_id):
    body = request.get_json()

    bet_type = request.args.get("type")

    if bet_type == SCORE:
        bet = ScoreBet.query.filter_by(user_id=current_user.id, id=bet_id).first()

        if "score" not in body["team1"] or "score" not in body["team2"]:
            raise WrongInputs()

    elif bet_type == BINARY:
        bet = BinaryBet.query.filter_by(user_id=current_user.id, id=bet_id).first()

        if "is_one_won" not in body:
            raise WrongInputs()

    else:
        raise InvalidBetType()

    if not bet:
        raise BetNotFound(bet_id)

    if is_locked(bet):
        raise LockedBets()

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

    response = {
        "phase": bet.match.group.phase.to_dict(),
        "group": bet.match.group.to_dict_without_phase(),
    }

    if bet_type == SCORE:
        response["score_bet"] = bet.to_dict_without_group()
    elif bet_type == BINARY:
        response["binary_bet"] = bet.to_dict_without_group()

    return success_response(200, response)


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


@bets.get(f"/{GLOBAL_ENDPOINT}/{VERSION}/bets/<string:bet_id>")
@token_required
def bet_get(current_user, bet_id):
    bet_type = request.args.get("type")

    if bet_type == SCORE:
        bet = ScoreBet.query.filter_by(user_id=current_user.id, id=bet_id).first()
    elif bet_type == BINARY:
        bet = BinaryBet.query.filter_by(user_id=current_user.id, id=bet_id).first()
    else:
        raise InvalidBetType()

    if not bet:
        raise BetNotFound(bet_id)

    response = {
        "phase": bet.match.group.phase.to_dict(),
        "group": bet.match.group.to_dict_without_phase(),
    }

    if bet_type == SCORE:
        response["score_bet"] = bet.to_dict_without_group()
    elif bet_type == BINARY:
        response["score_bet"] = bet.to_dict_without_group()

    return success_response(200, response)


@bets.post(f"/{GLOBAL_ENDPOINT}/{VERSION}/bets/finale_phase")
@token_required
def commit_finale_phase(current_user):
    finale_phase_config = current_app.config["FINALE_PHASE_CONFIG"]

    groups_result = {
        group.code: get_result_with_group_code(current_user.id, group.code)["results"]
        for group in Group.query.join(Group.phase).filter(Phase.code == "GROUP")
    }

    first_phase_phase_group = Group.query.filter_by(
        code=finale_phase_config["first_group"]
    ).first()

    existing_binary_bets = BinaryBet.query.join(BinaryBet.match).filter(
        and_(
            BinaryBet.user_id == current_user.id,
            Match.group_id == first_phase_phase_group.id,
        )
    )

    existing_matches = map(attrgetter("match"), existing_binary_bets)

    new_binary_bets = []
    new_matches = []

    for index, match_config in enumerate(finale_phase_config["versus"], 1):
        if all(
            team["played"] == 3
            for team in groups_result[match_config["team1"]["group"]]
        ) and all(
            team["played"] == 3
            for team in groups_result[match_config["team2"]["group"]]
        ):
            team1 = groups_result[match_config["team1"]["group"]][
                match_config["team1"]["rank"] - 1
            ]
            team2 = groups_result[match_config["team2"]["group"]][
                match_config["team2"]["rank"] - 1
            ]

            match = Match.query.filter_by(
                group_id=first_phase_phase_group.id,
                team1_id=team1["id"],
                team2_id=team2["id"],
                index=index,
            ).first()

            if not match:
                match = Match(
                    id=str(uuid4()),
                    group_id=first_phase_phase_group.id,
                    team1_id=team1["id"],
                    team2_id=team2["id"],
                    index=index,
                )

            new_matches.append(match)

            bet = BinaryBet.query.filter_by(
                user_id=current_user.id,
                match_id=match.id,
            ).first()

            if not bet:
                bet = BinaryBet(
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
        for bet in BinaryBet.query.filter_by(user_id=current_user.id):
            if bet.match.group.code in Group.query.join(Group.phase).filter(
                and_(Phase.code == "FINAL", Group.id == first_phase_phase_group.id)
            ):
                db.session.delete(bet)
        db.session.commit()

    phase, groups, score_bets, binary_bets = bets_from_phase_code(current_user, "FINAL")

    return success_response(
        200,
        {
            "phase": phase.to_dict(),
            "groups": [group.to_dict_without_phase() for group in groups],
            "score_bets": [
                score_bet.to_dict_with_group_id() for score_bet in score_bets
            ],
            "binary_bets": [
                binary_bet.to_dict_with_group_id() for binary_bet in binary_bets
            ],
        },
    )
