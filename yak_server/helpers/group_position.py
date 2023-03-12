from enum import Enum, unique

from yak_server.database.models import GroupPositionModel


@unique
class BetState(Enum):
    ANY_NONE = 1
    DRAWN = 2
    ONE_WIN = 3
    TWO_WIN = 4


def get_bet_state(score1, score2):
    if score1 is None or score2 is None:
        return BetState.ANY_NONE

    if score1 == score2:
        return BetState.DRAWN

    if score1 > score2:
        return BetState.ONE_WIN

    return BetState.TWO_WIN


def create_group_position(score_bets):
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


def update_group_position(
    old_score1,
    old_score2,
    new_score1,
    new_score2,
    group_position_team1,
    group_position_team2,
):
    old_bet_type = get_bet_state(old_score1, old_score2)
    new_bet_type = get_bet_state(new_score1, new_score2)

    if old_bet_type == BetState.ANY_NONE and new_bet_type == BetState.ANY_NONE:
        return

    elif old_bet_type == BetState.ANY_NONE:
        group_position_team1.goals_for += new_score1
        group_position_team1.goals_against += new_score2
        group_position_team2.goals_for += new_score2
        group_position_team2.goals_against += new_score1

    elif new_bet_type == BetState.ANY_NONE:
        group_position_team1.goals_for -= old_score1
        group_position_team1.goals_against -= old_score2
        group_position_team2.goals_for -= old_score2
        group_position_team2.goals_against -= old_score1

    else:
        group_position_team1.goals_for += new_score1 - old_score1
        group_position_team1.goals_against += new_score2 - old_score2
        group_position_team2.goals_for += new_score2 - old_score2
        group_position_team2.goals_against += new_score1 - old_score1

    if old_bet_type == BetState.DRAWN:
        group_position_team1.drawn -= 1
        group_position_team2.drawn -= 1

    if old_bet_type == BetState.ONE_WIN:
        group_position_team1.won -= 1
        group_position_team2.lost -= 1

    if old_bet_type == BetState.TWO_WIN:
        group_position_team1.lost -= 1
        group_position_team2.won -= 1

    if new_bet_type == BetState.DRAWN:
        group_position_team1.drawn += 1
        group_position_team2.drawn += 1

    if new_bet_type == BetState.ONE_WIN:
        group_position_team1.won += 1
        group_position_team2.lost += 1

    if new_bet_type == BetState.TWO_WIN:
        group_position_team1.lost += 1
        group_position_team2.won += 1
