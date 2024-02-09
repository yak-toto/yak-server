import sys

if sys.version_info >= (3, 9):
    from typing import Annotated
else:
    from typing_extensions import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from yak_server.database.models import LobbyModel, UserModel
from yak_server.helpers.database import get_db
from yak_server.helpers.lobby import generate_lobby_code
from yak_server.v1.helpers.auth import get_admin_user
from yak_server.v1.models.lobbies import LobbyOut

router = APIRouter(prefix="/lobbies", tags=["lobbies"])


@router.post("/")
def create_lobby(
    _: Annotated[UserModel, Depends(get_admin_user)],
    db: Annotated[Session, Depends(get_db)],
) -> LobbyOut:
    lobby = LobbyModel(code=generate_lobby_code())

    db.add(lobby)
    db.commit()

    return LobbyOut(id=lobby.id, code=lobby.code)
