from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session
from strawberry.fastapi import BaseContext

from yak_server.helpers.database import get_db
from yak_server.helpers.settings import Settings, get_settings


class YakContext(BaseContext):
    db: Session
    settings: Settings

    def __init__(self, db: Session, settings: Settings) -> None:
        super().__init__()
        self.db = db
        self.settings = settings


def get_context(
    db: Annotated[Session, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> YakContext:
    return YakContext(db, settings)
