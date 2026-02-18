from collections.abc import Iterable
from typing import TYPE_CHECKING

from pydantic import UUID4
from sqlalchemy.orm import selectinload

from .models import BinaryBetModel, GroupModel, MatchModel, PhaseModel, ScoreBetModel

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

    from .models import UserModel


def bets_from_group_id(
    db: "Session",
    user: "UserModel",
    group_id: UUID4,
) -> tuple[GroupModel | None, Iterable[ScoreBetModel], Iterable[BinaryBetModel]]:
    group = (
        db.query(GroupModel).options(selectinload(GroupModel.phase)).filter_by(id=group_id).first()
    )

    if group is None:
        return None, [], []

    score_bets = (
        db
        .query(ScoreBetModel)
        .options(
            selectinload(ScoreBetModel.match).selectinload(MatchModel.team1),
            selectinload(ScoreBetModel.match).selectinload(MatchModel.team2),
        )
        .join(ScoreBetModel.match)
        .where(MatchModel.user_id == user.id, MatchModel.group_id == group.id)
        .order_by(MatchModel.index)
    )

    binary_bets = (
        db
        .query(BinaryBetModel)
        .options(
            selectinload(BinaryBetModel.match).selectinload(MatchModel.team1),
            selectinload(BinaryBetModel.match).selectinload(MatchModel.team2),
        )
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
    PhaseModel | None,
    Iterable[GroupModel],
    Iterable[ScoreBetModel],
    Iterable[BinaryBetModel],
]:
    phase = db.query(PhaseModel).filter_by(code=phase_code).first()

    if not phase:
        return None, [], [], []

    groups = db.query(GroupModel).filter_by(phase_id=phase.id).order_by(GroupModel.index)

    binary_bets = (
        db
        .query(BinaryBetModel)
        .options(
            selectinload(BinaryBetModel.match).selectinload(MatchModel.team1),
            selectinload(BinaryBetModel.match).selectinload(MatchModel.team2),
        )
        .join(BinaryBetModel.match)
        .join(MatchModel.group)
        .where(MatchModel.user_id == user.id, GroupModel.phase_id == phase.id)
        .order_by(GroupModel.index, MatchModel.index)
    )

    score_bets = (
        db
        .query(ScoreBetModel)
        .options(
            selectinload(ScoreBetModel.match).selectinload(MatchModel.team1),
            selectinload(ScoreBetModel.match).selectinload(MatchModel.team2),
        )
        .join(ScoreBetModel.match)
        .join(MatchModel.group)
        .where(MatchModel.user_id == user.id, GroupModel.phase_id == phase.id)
        .order_by(GroupModel.index, MatchModel.index)
    )

    return phase, groups, score_bets, binary_bets
