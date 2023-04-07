from itertools import chain

from sqlalchemy import and_

from yak_server import db
from yak_server.database.models import BinaryBetModel, GroupModel, MatchModel, PhaseModel
from yak_server.v1.bets import get_group_rank_with_code


def compute_finale_phase_from_group_rank(user, rule_config):
    first_phase_phase_group = GroupModel.query.filter_by(
        code=rule_config["to_group"],
    ).first()

    groups_result = {
        group.code: get_group_rank_with_code(user, group.code)["group_rank"]
        for group in GroupModel.query.join(GroupModel.phase).filter(
            PhaseModel.code == rule_config["from_phase"],
        )
    }

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

            binary_bet = (
                BinaryBetModel.query.join(BinaryBetModel.match)
                .filter(
                    and_(
                        MatchModel.index == index,
                        BinaryBetModel.user_id == user.id,
                        MatchModel.group_id == first_phase_phase_group.id,
                    ),
                )
                .first()
            )

            binary_bet.match.team1_id = team1["id"]
            binary_bet.match.team2_id = team2["id"]

            db.session.flush()

    db.session.commit()


RULE_MAPPING = {
    "492345de-8d4a-45b6-8b94-d219f2b0c3e9": compute_finale_phase_from_group_rank,
}
