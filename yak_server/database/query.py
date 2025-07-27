from collections.abc import Iterable
from typing import TYPE_CHECKING, Optional

from sqlmodel import Session, select

from .models import BinaryBetModel, GroupModel, MatchModel, PhaseModel, ScoreBetModel

if TYPE_CHECKING:
    from sqlmodel import Session

    from .models import UserModel


def bets_from_group_code(
    db: "Session",
    user: "UserModel",
    group_code: str,
) -> tuple[Optional[GroupModel], Iterable[ScoreBetModel], Iterable[BinaryBetModel]]:
    group = db.exec(select(GroupModel).where(GroupModel.code == group_code)).first()

    if not group:
        return None, [], []

    score_bets = db.exec(
        select(ScoreBetModel)
        .join(ScoreBetModel.match)
        .where(MatchModel.user_id == user.id, MatchModel.group_id == group.id)
        .order_by(MatchModel.index)
    )

    binary_bets = db.exec(
        select(BinaryBetModel)
        .join(BinaryBetModel.match)
        .where(MatchModel.user_id == user.id, MatchModel.group_id == group.id)
        .order_by(MatchModel.index)
    )

    return group, score_bets, binary_bets


def bets_from_phase_code(
    db: "Session",
    user: "UserModel",
    phase_code: str,
) -> tuple[
    Optional[PhaseModel], Iterable[GroupModel], Iterable[ScoreBetModel], Iterable[BinaryBetModel]
]:
    phase = db.exec(select(PhaseModel).where(PhaseModel.code == phase_code)).first()

    if not phase:
        return None, [], [], []

    groups = db.exec(
        select(GroupModel).where(GroupModel.phase_id == phase.id).order_by(GroupModel.index)
    )

    binary_bets = db.exec(
        select(BinaryBetModel)
        .join(BinaryBetModel.match)
        .join(MatchModel.group)
        .where(MatchModel.user_id == user.id, GroupModel.phase_id == phase.id)
        .order_by(GroupModel.index, MatchModel.index)
    )

    score_bets = db.exec(
        select(ScoreBetModel)
        .join(ScoreBetModel.match)
        .join(MatchModel.group)
        .where(MatchModel.user_id == user.id, GroupModel.phase_id == phase.id)
        .order_by(GroupModel.index, MatchModel.index)
    )

    return phase, groups, score_bets, binary_bets
