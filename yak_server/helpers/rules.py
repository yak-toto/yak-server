from itertools import chain
from operator import attrgetter
from uuid import uuid4

from sqlalchemy import and_

from yak_server import db
from yak_server.database.models import BinaryBetModel, GroupModel, MatchModel, PhaseModel
from yak_server.v1.bets import get_group_rank_with_code


def compute_finale_phase_from_group_rank(user, rule_config):
    groups_result = {
        group.code: get_group_rank_with_code(user, group.code)["group_rank"]
        for group in GroupModel.query.join(GroupModel.phase).filter(
            PhaseModel.code == rule_config["first_phase"],
        )
    }

    first_phase_phase_group = GroupModel.query.filter_by(
        code=rule_config["first_group"],
    ).first()

    existing_binary_bets = BinaryBetModel.query.join(BinaryBetModel.match).filter(
        and_(
            BinaryBetModel.user_id == user.id,
            MatchModel.group_id == first_phase_phase_group.id,
        ),
    )

    new_binary_bets = []
    new_matches = []

    for index, match_config in enumerate(rule_config["versus"], 1):
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
                user_id=user.id,
                match_id=match.id,
            ).first()

            if not bet:
                bet = BinaryBetModel(
                    user_id=user.id,
                    match_id=match.id,
                )

            new_binary_bets.append(bet)

    # Compare existing matches/bets and new matches/bets
    db.session.add_all(new_matches)
    db.session.flush()

    db.session.add_all(new_binary_bets)
    db.session.flush()

    is_bet_modified = False

    for bet in existing_binary_bets:
        if bet.id not in map(attrgetter("id"), new_binary_bets):
            is_bet_modified = True
            db.session.delete(bet)

    db.session.flush()

    if is_bet_modified:
        for bet in BinaryBetModel.query.filter_by(user_id=user.id):
            if bet.match.group.code in GroupModel.query.join(GroupModel.phase).filter(
                and_(
                    PhaseModel.code == rule_config["second_phase"],
                    GroupModel.id == first_phase_phase_group.id,
                ),
            ):
                db.session.delete(bet)
        db.session.flush()

    db.session.commit()


RULE_MAPPING = {
    "492345de-8d4a-45b6-8b94-d219f2b0c3e9": compute_finale_phase_from_group_rank,
}
