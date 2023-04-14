from typing import TYPE_CHECKING, List, Tuple

from .models import BinaryBetModel, GroupModel, MatchModel, PhaseModel, ScoreBetModel

if TYPE_CHECKING:
    from .models import UserModel


def bets_from_group_code(
    user: "UserModel",
    group_code: str,
) -> Tuple[GroupModel, List[ScoreBetModel], List[BinaryBetModel]]:
    group = GroupModel.query.filter_by(code=group_code).first()

    if not group:
        return None, [], []

    score_bets = (
        user.score_bets.filter(MatchModel.group_id == group.id)
        .join(ScoreBetModel.match)
        .order_by(MatchModel.index)
    )

    binary_bets = (
        user.binary_bets.filter(MatchModel.group_id == group.id)
        .join(BinaryBetModel.match)
        .order_by(MatchModel.index)
    )

    return group, score_bets, binary_bets


def bets_from_phase_code(
    user: "UserModel",
    phase_code: str,
) -> Tuple[PhaseModel, List[GroupModel], List[ScoreBetModel], List[BinaryBetModel]]:
    phase = PhaseModel.query.filter_by(code=phase_code).first()

    if not phase:
        return None, [], [], []

    groups = GroupModel.query.filter_by(phase_id=phase.id).order_by(GroupModel.index)

    binary_bets = (
        user.binary_bets.filter(GroupModel.phase_id == phase.id)
        .join(BinaryBetModel.match)
        .join(MatchModel.group)
        .order_by(GroupModel.index, MatchModel.index)
    )

    score_bets = (
        user.score_bets.filter(GroupModel.phase_id == phase.id)
        .join(ScoreBetModel.match)
        .join(MatchModel.group)
        .order_by(GroupModel.index, MatchModel.index)
    )

    return phase, groups, score_bets, binary_bets
