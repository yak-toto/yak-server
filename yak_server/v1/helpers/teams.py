from pydantic import UUID4
from sqlalchemy.orm import Session

from yak_server.database.models import TeamModel
from yak_server.v1.helpers.errors import TeamNotFound


def validate_team_id(db: Session, team_id: UUID4 | None) -> None:
    if team_id is not None and db.get(TeamModel, team_id) is None:
        raise TeamNotFound(team_id)
