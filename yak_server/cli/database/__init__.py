import json
import logging
from pathlib import Path
from typing import TYPE_CHECKING

from yak_server.database import build_engine, build_local_session_maker
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
from yak_server.helpers.authentication import signup_user
from yak_server.helpers.rules.compute_points import compute_points as compute_points_func
from yak_server.helpers.settings import get_settings

try:
    import alembic
except ImportError:  # pragma: no cover
    # Very common pattern for optional dependency imports
    alembic = None  # type: ignore[assignment]

if TYPE_CHECKING:
    from fastapi import FastAPI

logger = logging.getLogger(__name__)


class RecordDeletionInProductionError(Exception):
    def __init__(self) -> None:
        super().__init__("Trying to delete records in production using script. DO NOT DO IT.")


class TableDropInProductionError(Exception):
    def __init__(self) -> None:
        super().__init__("Trying to drop database tables in production using script. DO NOT DO IT.")


def create_database() -> None:
    local_session_maker = build_local_session_maker()

    with local_session_maker():
        Base.metadata.create_all(bind=build_engine())


def create_admin(password: str) -> None:
    local_session_maker = build_local_session_maker()

    with local_session_maker() as db:
        _ = signup_user(db, name="admin", first_name="admin", last_name="admin", password=password)


def initialize_database(app: "FastAPI") -> None:
    local_session_maker = build_local_session_maker()

    with local_session_maker() as db:
        data_folder = get_settings().data_folder

        phases = json.loads(Path(data_folder, "phases.json").read_text(encoding="utf-8"))

        db.add_all(PhaseModel(**phase) for phase in phases)
        db.flush()

        groups = json.loads(Path(data_folder, "groups.json").read_text(encoding="utf-8"))

        for group in groups:
            phase = db.query(PhaseModel).filter_by(code=group.pop("phase_code")).first()
            group["phase_id"] = phase.id

        db.add_all(GroupModel(**group) for group in groups)
        db.flush()

        teams = json.loads(Path(data_folder, "teams.json").read_text(encoding="utf-8"))

        for team in teams:
            team["flag_url"] = ""

            team_instance = TeamModel(**team)
            db.add(team_instance)
            db.flush()

            team_instance.flag_url = app.url_path_for(
                "retrieve_team_flag_by_id",
                team_id=team_instance.id,
            )
            db.flush()

        matches = json.loads(Path(data_folder, "matches.json").read_text(encoding="utf-8"))

        for match in matches:
            team1_code = match.pop("team1_code")
            team2_code = match.pop("team2_code")

            if team1_code is None:
                match["team1_id"] = None
            else:
                team1 = db.query(TeamModel).filter_by(code=team1_code).first()
                match["team1_id"] = team1.id

            if team2_code is None:
                match["team2_id"] = None
            else:
                team2 = db.query(TeamModel).filter_by(code=team2_code).first()
                match["team2_id"] = team2.id

            group = db.query(GroupModel).filter_by(code=match.pop("group_code")).first()
            match["group_id"] = group.id

        db.add_all(MatchReferenceModel(**match) for match in matches)
        db.flush()

        db.commit()


def delete_database(app: "FastAPI") -> None:
    if not app.debug:
        raise RecordDeletionInProductionError

    local_session_maker = build_local_session_maker()

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


def drop_database(app: "FastAPI") -> None:
    if not app.debug:
        raise TableDropInProductionError

    local_session_maker = build_local_session_maker()

    with local_session_maker():
        Base.metadata.drop_all(bind=build_engine())


def print_export_command(alembic_ini_path: Path) -> None:
    print(f"export ALEMBIC_CONFIG={alembic_ini_path}")


def setup_migration(*, short: bool = False) -> None:
    alembic_ini_path = (Path(__file__).parents[2] / "alembic.ini").resolve()

    if not alembic_ini_path.exists():
        alembic_ini_path = (Path(__file__).parents[3] / "alembic.ini").resolve()

    if short is True:
        print_export_command(alembic_ini_path)
    else:
        print(
            "To be able to run the database migration scripts, "
            "you need to run the following command:",
        )
        print_export_command(alembic_ini_path)
        print()
        print(
            "Follow this link for more information: "
            "https://alembic.sqlalchemy.org/en/latest/tutorial.html#editing-the-ini-file",
        )

        if alembic is None:
            print()
            print(
                "To enable migration using alembic, please run: "
                "uv pip install yak-server[db_migration]"
            )


def compute_score_board() -> None:
    local_session_maker = build_local_session_maker()

    with local_session_maker() as db:
        admin = db.query(UserModel).filter_by(name="admin").first()

        rule_config = get_settings().rules.compute_points

        compute_points_func(db, admin, rule_config)
