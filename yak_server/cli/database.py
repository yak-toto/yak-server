import json
from pathlib import Path
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import update
from sqlalchemy.dialects.postgresql import insert

from yak_server.database.models import (
    Base,
    BinaryBetModel,
    GroupModel,
    GroupPositionModel,
    MatchModel,
    MatchReferenceModel,
    PhaseModel,
    ScoreBetModel,
    TeamModel,
    UserModel,
)
from yak_server.database.session import build_local_session_maker

if TYPE_CHECKING:
    from fastapi import FastAPI
    from sqlalchemy import Engine
    from sqlalchemy.orm import Session


class RecordDeletionInProductionError(Exception):
    def __init__(self) -> None:
        super().__init__("Trying to delete records in production using script. DO NOT DO IT.")


class TableDropInProductionError(Exception):
    def __init__(self) -> None:
        super().__init__("Trying to drop database tables in production using script. DO NOT DO IT.")


def create_database(engine: "Engine") -> None:
    Base.metadata.create_all(bind=engine)


class MissingPhaseDuringInitError(Exception):
    def __init__(self, phase_code: str) -> None:
        super().__init__(
            f"Error during database initialization: phase_code={phase_code} not found.",
        )


class MissingTeamDuringInitError(Exception):
    def __init__(self, team_code: str) -> None:
        super().__init__(f"Error during database initialization: team_code={team_code} not found.")


class MissingGroupDuringInitError(Exception):
    def __init__(self, group_code: str) -> None:
        super().__init__(
            f"Error during database initialization: group_code={group_code} not found.",
        )


def fetch_team_id(team_code: str | None, db: "Session") -> UUID | None:
    if team_code is None:
        return None

    team = db.query(TeamModel).filter_by(code=team_code).first()

    if team is None:
        raise MissingTeamDuringInitError(team_code)

    return team.id


def fetch_group_id(group_code: str, db: "Session") -> UUID:
    group = db.query(GroupModel).filter_by(code=group_code).first()

    if group is None:
        raise MissingGroupDuringInitError(group_code)

    return group.id


def initialize_database(engine: "Engine", app: "FastAPI", data_folder: Path) -> None:
    local_session_maker = build_local_session_maker(engine)

    with local_session_maker() as db:
        phases = json.loads((data_folder / "phases.json").read_text(encoding="utf-8"))

        for phase in phases:
            db.execute(
                insert(PhaseModel).values(**phase).on_conflict_do_nothing(index_elements=["code"]),
            )

        db.flush()

        groups = json.loads((data_folder / "groups.json").read_text(encoding="utf-8"))

        for group in groups:
            phase_code = group.pop("phase_code")

            phase = db.query(PhaseModel).filter_by(code=phase_code).first()

            if phase is None:
                raise MissingPhaseDuringInitError(phase_code)

            group["phase_id"] = phase.id

        for group in groups:
            db.execute(
                insert(GroupModel).values(**group).on_conflict_do_nothing(index_elements=["code"]),
            )

        db.flush()

        teams = json.loads((data_folder / "teams.json").read_text(encoding="utf-8"))

        for team in teams:
            team["flag_url"] = ""

            db.execute(
                insert(TeamModel).values(**team).on_conflict_do_nothing(index_elements=["code"]),
            )

            db.flush()

            team_instance = db.query(TeamModel).filter_by(code=team["code"]).first()

            if team_instance is None:  # pragma: no cover
                raise MissingTeamDuringInitError(team_code=team["code"])

            update_flag_url_stmt = (
                update(TeamModel)
                .where(TeamModel.code == team["code"])
                .values(
                    flag_url=app.url_path_for("retrieve_team_flag_by_id", team_id=team_instance.id),
                )
            )

            db.execute(update_flag_url_stmt)
            db.flush()

        matches = json.loads((data_folder / "matches.json").read_text(encoding="utf-8"))

        for match in matches:
            match["team1_id"] = fetch_team_id(match.pop("team1_code"), db)
            match["team2_id"] = fetch_team_id(match.pop("team2_code"), db)
            match["group_id"] = fetch_group_id(match.pop("group_code"), db)

        for match in matches:
            db.execute(
                insert(MatchReferenceModel)
                .values(**match)
                .on_conflict_do_nothing(index_elements=["group_id", "index"]),
            )

        db.flush()

        db.commit()


def delete_database(engine: "Engine", *, debug: bool) -> None:
    if debug is False:
        raise RecordDeletionInProductionError

    local_session_maker = build_local_session_maker(engine)

    with local_session_maker() as db:
        db.query(GroupPositionModel).delete()
        db.query(ScoreBetModel).delete()
        db.query(BinaryBetModel).delete()
        db.query(MatchReferenceModel).delete()
        db.query(MatchModel).delete()
        db.query(UserModel).delete()
        db.query(GroupModel).delete()
        db.query(PhaseModel).delete()
        db.query(TeamModel).delete()
        db.commit()


def drop_database(engine: "Engine", *, debug: bool) -> None:
    if debug is False:
        raise TableDropInProductionError

    Base.metadata.drop_all(bind=engine)
