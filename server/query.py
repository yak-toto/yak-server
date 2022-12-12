from itertools import chain

from .models import BinaryBet
from .models import Group
from .models import Match
from .models import Phase
from .models import ScoreBet


def bets_from_group_code(user, group_code):
    group = Group.query.filter_by(code=group_code).first()

    score_bets = (
        user.bets.filter(Match.group_id == group.id)
        .join(ScoreBet.match)
        .order_by(Match.index)
    )

    binary_bets = (
        user.binary_bets.filter(Match.group_id == group.id)
        .join(BinaryBet.match)
        .order_by(Match.index)
    )

    return group, score_bets, binary_bets


def matches_from_group_code(user, group_code):
    group, score_bets, binary_bets = bets_from_group_code(user, group_code)

    return group, (bet.match for bet in chain(score_bets, binary_bets))


def bets_from_phase_code(user, phase_code):
    phase = Phase.query.filter_by(code=phase_code).first()

    groups = Group.query.filter_by(phase_id=phase.id).order_by(Group.code)

    binary_bets = (
        user.binary_bets.filter(Group.phase_id == phase.id)
        .join(BinaryBet.match)
        .join(Match.group)
        .order_by(Group.code, Match.index)
    )

    score_bets = (
        user.bets.filter(Group.phase_id == phase.id)
        .join(ScoreBet.match)
        .join(Match.group)
        .order_by(Group.code, Match.index)
    )

    return phase, groups, score_bets, binary_bets


def matches_from_phase_code(user, phase_code):
    phase, groups, score_bets, binary_bets = bets_from_phase_code(user, phase_code)

    return phase, groups, (bet.match for bet in chain(score_bets, binary_bets))
