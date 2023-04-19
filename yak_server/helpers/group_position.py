from dataclasses import dataclass
from typing import TYPE_CHECKING, List

from yak_server.database.models import GroupPositionModel, MatchModel, ScoreBetModel

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

    from yak_server.database.models import UserModel


def create_group_position(score_bets: List["ScoreBetModel"]) -> List[GroupPositionModel]:
    team_ids = []

    group_positions = []

    for score_bet in score_bets:
        if score_bet.match.team1_id not in team_ids:
            group_positions.append(
                GroupPositionModel(
                    team_id=score_bet.match.team1_id,
                    user_id=score_bet.user.id,
                    group_id=score_bet.match.group.id,
                ),
            )
            team_ids.append(score_bet.match.team1_id)

        if score_bet.match.team2_id not in team_ids:
            group_positions.append(
                GroupPositionModel(
                    team_id=score_bet.match.team2_id,
                    user_id=score_bet.user.id,
                    group_id=score_bet.match.group.id,
                ),
            )
            team_ids.append(score_bet.match.team2_id)

    return group_positions


@dataclass
class GroupPosition:
    won: int = 0
    drawn: int = 0
    lost: int = 0
    goals_for: int = 0
    goals_against: int = 0


def compute_group_rank(
    group_rank: List[GroupPositionModel],
    score_bets: List["ScoreBetModel"],
) -> List[GroupPositionModel]:
    new_group_position = {}

    for score_bet in score_bets:
        team1_id = score_bet.match.team1_id
        team2_id = score_bet.match.team2_id

        if team1_id not in new_group_position:
            new_group_position[team1_id] = GroupPosition()

        if team2_id not in new_group_position:
            new_group_position[team2_id] = GroupPosition()

        if score_bet.score1 is None or score_bet.score2 is None:
            continue

        new_group_position[team1_id].goals_for += score_bet.score1
        new_group_position[team1_id].goals_against += score_bet.score2
        new_group_position[team2_id].goals_for += score_bet.score2
        new_group_position[team2_id].goals_against += score_bet.score1

        if score_bet.score1 > score_bet.score2:
            new_group_position[team1_id].won += 1
            new_group_position[team2_id].lost += 1
        elif score_bet.score1 == score_bet.score2:
            new_group_position[team1_id].drawn += 1
            new_group_position[team2_id].drawn += 1
        else:
            new_group_position[team1_id].lost += 1
            new_group_position[team2_id].won += 1

    for group_position in group_rank:
        group_position.won = new_group_position[group_position.team_id].won
        group_position.drawn = new_group_position[group_position.team_id].drawn
        group_position.lost = new_group_position[group_position.team_id].lost
        group_position.goals_for = new_group_position[group_position.team_id].goals_for
        group_position.goals_against = new_group_position[group_position.team_id].goals_against
        group_position.need_recomputation = False

    return sorted(
        group_rank,
        key=lambda team_result: (
            team_result.points,
            team_result.goals_difference,
            team_result.goals_for,
        ),
        reverse=True,
    )


def get_group_rank_with_code(
    db: "Session",
    user: "UserModel",
    group_id: str,
) -> List[GroupPositionModel]:
    group_rank = db.query(GroupPositionModel).filter_by(group_id=group_id, user_id=user.id)

    if not any(group_position.need_recomputation for group_position in group_rank):
        return sorted(
            group_rank,
            key=lambda team_result: (
                team_result.points,
                team_result.goals_difference,
                team_result.goals_for,
            ),
            reverse=True,
        )

    score_bets = user.score_bets.filter(MatchModel.group_id == group_id).join(ScoreBetModel.match)

    group_rank = compute_group_rank(group_rank, score_bets)

    db.commit()

    return sorted(
        group_rank,
        key=lambda team_result: (
            team_result.points,
            team_result.goals_difference,
            team_result.goals_for,
        ),
        reverse=True,
    )
