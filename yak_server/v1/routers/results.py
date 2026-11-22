from typing import TYPE_CHECKING
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from yak_server.database.models import GroupModel, Role, UserKnockoutGuessModel, UserModel
from yak_server.helpers.database import SessionDep
from yak_server.helpers.language import DEFAULT_LANGUAGE, LangQuery
from yak_server.v1.helpers.auth import CurrentUserDep, require_user
from yak_server.v1.helpers.responses import error_responses
from yak_server.v1.models.generic import GenericOut
from yak_server.v1.models.groups import GroupOut
from yak_server.v1.models.results import ScoreBoardResponse, ScoreBoardUserResult, UserResult

if TYPE_CHECKING:
    from collections.abc import Sequence


router = APIRouter(
    tags=["results"],
    dependencies=[Depends(require_user)],
    responses=error_responses(status.HTTP_401_UNAUTHORIZED),
)


@router.get("/score_board")
def retrieve_score_board(
    db: SessionDep,
    lang: LangQuery = DEFAULT_LANGUAGE,
) -> GenericOut[ScoreBoardResponse]:
    knockout_groups = (
        db
        .query(GroupModel)
        .where(GroupModel.id.in_(select(UserKnockoutGuessModel.group_id).distinct()))
        .order_by(GroupModel.index)
        .all()
    )

    users = list(
        db
        .query(UserModel)
        .options(
            selectinload(UserModel.knockout_guesses).selectinload(UserKnockoutGuessModel.group)
        )
        .order_by(UserModel.points.desc())
        .where(UserModel.role != Role.ADMIN)
    )

    return GenericOut(
        result=ScoreBoardResponse(
            groups=[GroupOut.from_instance(g, lang=lang) for g in knockout_groups],
            results=[
                ScoreBoardUserResult.from_instance(user, rank=rank)
                for rank, user in enumerate(users, 1)
            ],
        )
    )


def compute_rank(db: Session, user_id: UUID) -> int:
    subq = (
        db
        .query(
            UserModel,
            func.row_number().over(order_by=UserModel.points.desc()).label("rownum"),
        )
        .where(UserModel.role != Role.ADMIN)
        .subquery()
    )

    rank: Sequence[int] = db.query(subq.c.rownum).where(subq.c.id == user_id).first()

    if not rank:
        return 0

    return rank[0]


@router.get("/results")
def retrieve_user_results(
    user: CurrentUserDep,
    db: SessionDep,
    lang: LangQuery = DEFAULT_LANGUAGE,
) -> GenericOut[UserResult]:
    rank = compute_rank(db, user.id)

    user_with_guesses = (
        db
        .query(UserModel)
        .options(
            selectinload(UserModel.knockout_guesses).selectinload(UserKnockoutGuessModel.group)
        )
        .filter_by(id=user.id)
        .one()
    )

    number_of_players = db.query(func.count(UserModel.id)).where(UserModel.name != "admin").scalar()

    return GenericOut(
        result=UserResult.from_instance(
            user_with_guesses, rank=rank, number_of_players=number_of_players, lang=lang
        )
    )
