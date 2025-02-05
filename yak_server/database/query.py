from typing import TYPE_CHECKING

from sqlmodel import select

from .models3 import BinaryBetModel, GroupModel, MatchModel, PhaseModel, ScoreBetModel

if TYPE_CHECKING:
    from sqlmodel import Session

    from .models3 import UserModel


def bets_from_group_code(
    db: "Session",
    user: "UserModel",
    group_code: str,
) -> tuple[GroupModel, list[ScoreBetModel], list[BinaryBetModel]]:
    group = db.exec(select(GroupModel).where(GroupModel.code == group_code)).first()

    if group is None:
        return None, [], []

    score_bets = db.exec(
        select(ScoreBetModel, MatchModel)
        .order_by(MatchModel.index)
        .where(MatchModel.user_id == user.id, MatchModel.group_id == group.id)
    )

    binary_bets = db.exec(
        select(BinaryBetModel, MatchModel)
        .order_by(MatchModel.index)
        .where(MatchModel.user_id == user.id, MatchModel.group_id == group.id)
    )

    return group, score_bets, binary_bets


def bets_from_phase_code(
    db: "Session",
    user: "UserModel",
    phase_code: str,
) -> tuple[PhaseModel, list[GroupModel], list[ScoreBetModel], list[BinaryBetModel]]:
    phase = db.exec(select(PhaseModel).where(PhaseModel.code == phase_code)).first()

    if not phase:
        return None, [], [], []

    groups = db.exec(
        select(GroupModel).order_by(GroupModel.index).where(GroupModel.phase_id == phase.id)
    )

    binary_bets = db.exec(
        select(BinaryBetModel)
        .order_by(GroupModel.index, MatchModel.index)
        .where(
            BinaryBetModel.match_id == MatchModel.id,
            MatchModel.group_id == GroupModel.id,
            MatchModel.user_id == user.id,
        )
    )

    score_bets = db.exec(
        select(ScoreBetModel)
        .order_by(GroupModel.index, MatchModel.index)
        .where(
            ScoreBetModel.match_id == MatchModel.id,
            MatchModel.group_id == GroupModel.id,
            MatchModel.user_id == user.id,
        )
    )

    return phase, groups, score_bets, binary_bets
