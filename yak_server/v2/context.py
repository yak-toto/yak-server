from __future__ import annotations

from typing import TYPE_CHECKING, Annotated

from strawberry.fastapi import BaseContext

if TYPE_CHECKING:
    from fastapi import Depends
    from sqlalchemy.orm import Session

    from yak_server.database.models import UserModel
    from yak_server.helpers.database import get_db
    from yak_server.helpers.settings import Settings, get_settings


class YakContext(BaseContext):
    db: Session
    settings: Settings
    user: UserModel | None

    def __init__(self, db: Session, settings: Settings, user: UserModel | None = None) -> None:
        super().__init__()
        self.db = db
        self.settings = settings
        self.user = user


def get_context(
    db: Annotated[Session, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> YakContext:
    return YakContext(db, settings)
