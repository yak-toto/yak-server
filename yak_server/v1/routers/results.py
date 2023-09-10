import sys
from typing import List

if sys.version_info >= (3, 9):
    from typing import Annotated
else:
    from typing_extensions import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from yak_server.database.models import (
    UserModel,
)
from yak_server.helpers.database import get_db
from yak_server.v1.helpers.auth import get_current_user
from yak_server.v1.helpers.errors import NoResultsForAdminUser
from yak_server.v1.models.generic import GenericOut
from yak_server.v1.models.results import UserResult

router = APIRouter(tags=["results"])


@router.get("/score_board")
def retrieve_score_board(
    _: Annotated[UserModel, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> GenericOut[List[UserResult]]:
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


@router.get("/results")
def retrieve_user_results(
    user: Annotated[UserModel, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> GenericOut[UserResult]:
    if user.name == "admin":
        raise NoResultsForAdminUser

    user_result = UserResult.from_instance(
        user,
        rank=next(
            index
            for index, user_result in enumerate(
                db.query(UserModel)
                .order_by(UserModel.points.desc())
                .filter(
                    UserModel.name != "admin",
                ),
                1,
            )
            if user_result.id == user.id
        ),
    )

    return GenericOut(result=user_result)
