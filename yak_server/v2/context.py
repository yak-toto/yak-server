from typing import Optional

from fastapi import Depends
from sqlalchemy.orm import Session
from strawberry.fastapi import BaseContext

from yak_server.database.models import UserModel
from yak_server.helpers.settings import Settings, get_settings
from yak_server.v1.helpers.database import get_db


class YakContext(BaseContext):
    db: Session
    settings: Settings
    user: Optional[UserModel]

    def __init__(self, db: Session, settings: Settings, user: Optional[UserModel] = None) -> None:
        super().__init__()
        self.db = db
        self.settings = settings
        self.user = user


def get_context(
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> YakContext:
    return YakContext(db, settings)
