from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import UUID4
from sqlalchemy.orm import Session

from yak_server.database.models import LobbyModel, UserModel
from yak_server.helpers.authentication import signup_user
from yak_server.helpers.database import get_db
from yak_server.v1.helpers.auth import get_admin_user, get_current_user
from yak_server.v1.helpers.errors import LobbyNotFound
from yak_server.v1.models.generic import GenericOut
from yak_server.v1.models.lobbies import LobbyIn, LobbyOut, LobbyOutWithUsers

router = APIRouter(prefix="/lobbies", tags=["lobbies"])


@router.post("/")
def create_lobby(
    lobby_in: LobbyIn,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[UserModel, Depends(get_admin_user)],
) -> GenericOut[LobbyOut]:
    lobby = LobbyModel(name=lobby_in.name)

    db.add(lobby)
    db.flush()

    signup_user(
        db,
        "official_results_" + lobby.id,
        "official_results",
        "official_results",
        lobby_in.official_results_password,
    )

    return GenericOut[LobbyOut](result=LobbyOut.from_instance(lobby))


@router.get("/{lobby_id}")
def get_lobby(
    lobby_id: UUID4, db: Annotated[Session, Depends(get_db)]
) -> GenericOut[LobbyOutWithUsers]:
    lobby = db.query(LobbyModel).filter_by(id=lobby_id).first()

    if lobby is None:
        raise LobbyNotFound(lobby_id)

    return GenericOut[LobbyOutWithUsers](result=LobbyOutWithUsers.from_instance(lobby))


@router.post("/{lobby_id}/users")
def add_user_to_lobby(
    lobby_id: UUID4,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[UserModel, Depends(get_current_user)],
) -> GenericOut[LobbyOutWithUsers]:
    lobby = db.query(LobbyModel).filter_by(id=lobby_id).first()

    if lobby is None:
        raise LobbyNotFound(lobby_id)

    user.lobby_id = lobby.id

    db.commit()

    return GenericOut[LobbyOutWithUsers](result=LobbyOutWithUsers.from_instance(lobby))
