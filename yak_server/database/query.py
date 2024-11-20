from typing import TYPE_CHECKING

from sqlalchemy import and_

from .models import BinaryBetModel, GroupModel, MatchModel, PhaseModel, ScoreBetModel

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

    from .models import UserModel


def bets_from_group_code(
    db: "Session",
    user: "UserModel",
    group_code: str,
) -> tuple[GroupModel, list[ScoreBetModel], list[BinaryBetModel]]:
    group = db.query(GroupModel).filter_by(code=group_code).first()

    if not group:
        return None, [], []

    score_bets = (
        db.query(ScoreBetModel)
        .join(ScoreBetModel.match)
        .filter(and_(MatchModel.user_id == user.id, MatchModel.group_id == group.id))
        .order_by(MatchModel.index)
    )

    binary_bets = (
        db.query(BinaryBetModel)
        .join(BinaryBetModel.match)
        .filter(and_(MatchModel.user_id == user.id, MatchModel.group_id == group.id))
        .order_by(MatchModel.index)
    )

    return group, score_bets, binary_bets


def bets_from_phase_code(
    db: "Session",
    user: "UserModel",
    phase_code: str,
) -> tuple[PhaseModel, list[GroupModel], list[ScoreBetModel], list[BinaryBetModel]]:
    phase = db.query(PhaseModel).filter_by(code=phase_code).first()

    if not phase:
        return None, [], [], []

    groups = db.query(GroupModel).filter_by(phase_id=phase.id).order_by(GroupModel.index)

    binary_bets = (
        db.query(BinaryBetModel)
        .join(BinaryBetModel.match)
        .join(MatchModel.group)
        .filter(and_(MatchModel.user_id == user.id, GroupModel.phase_id == phase.id))
        .order_by(GroupModel.index, MatchModel.index)
    )

    score_bets = (
        db.query(ScoreBetModel)
        .join(ScoreBetModel.match)
        .join(MatchModel.group)
        .filter(and_(MatchModel.user_id == user.id, GroupModel.phase_id == phase.id))
        .order_by(GroupModel.index, MatchModel.index)
    )

    return phase, groups, score_bets, binary_bets
