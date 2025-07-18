from typing import TYPE_CHECKING, Annotated, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from yak_server.database.models import UserModel
from yak_server.helpers.database import get_db
from yak_server.v1.helpers.auth import get_current_user
from yak_server.v1.helpers.errors import NoResultsForAdminUser
from yak_server.v1.models.generic import ErrorOut, GenericOut, ValidationErrorOut
from yak_server.v1.models.results import UserResult

if TYPE_CHECKING:
    from collections.abc import Sequence


router = APIRouter(tags=["results"])


@router.get(
    "/score_board",
    responses={
        status.HTTP_401_UNAUTHORIZED: {"model": ErrorOut},
        status.HTTP_422_UNPROCESSABLE_ENTITY: {"model": ValidationErrorOut},
    },
)
def retrieve_score_board(
    _: Annotated[UserModel, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> GenericOut[list[UserResult]]:
    return GenericOut(
        result=[
            UserResult.from_instance(user, rank=rank)
            for rank, user in enumerate(
                db.query(UserModel)
                .order_by(UserModel.points.desc())
                .where(UserModel.name != "admin"),
                1,
            )
        ],
    )


def compute_rank(db: Session, user_id: UUID) -> Optional[int]:
    subq = (
        db.query(
            UserModel,
            func.row_number().over(order_by=UserModel.points.desc()).label("rownum"),
        )
        .filter(UserModel.name != "admin")
        .subquery()
    )

    rank: Sequence[int] = db.query(subq.c.rownum).filter(subq.c.id == user_id).first()

    if not rank:
        return None

    return rank[0]


@router.get(
    "/results",
    responses={
        status.HTTP_401_UNAUTHORIZED: {"model": ErrorOut},
        status.HTTP_422_UNPROCESSABLE_ENTITY: {"model": ValidationErrorOut},
    },
)
def retrieve_user_results(
    user: Annotated[UserModel, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> GenericOut[UserResult]:
    rank = compute_rank(db, user.id)

    if rank is None:
        raise NoResultsForAdminUser

    user_result = UserResult.from_instance(
        user,
        rank=rank,
    )

    return GenericOut(result=user_result)
