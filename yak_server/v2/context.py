from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import Depends
from strawberry.fastapi import BaseContext

from yak_server.config_file import Settings, get_settings
from yak_server.v1.helpers.database import get_db

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

    from yak_server.database.models import UserModel


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
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> YakContext:
    return YakContext(db, settings)
