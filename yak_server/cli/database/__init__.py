import json
import logging
from pathlib import Path
from typing import TYPE_CHECKING

from yak_server.database import build_local_session_maker
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
from yak_server.v1.helpers.errors import NoAdminUser

try:
    import alembic
except ImportError:  # pragma: no cover
    # Very common pattern for optional dependency imports
    alembic = None  # type: ignore[assignment]

if TYPE_CHECKING:
    from fastapi import FastAPI
    from sqlalchemy import Engine

logger = logging.getLogger(__name__)


class RecordDeletionInProductionError(Exception):
    def __init__(self) -> None:
        super().__init__("Trying to delete records in production using script. DO NOT DO IT.")


class TableDropInProductionError(Exception):
    def __init__(self) -> None:
        super().__init__("Trying to drop database tables in production using script. DO NOT DO IT.")


def create_database(engine: "Engine") -> None:
    Base.metadata.create_all(bind=engine)


def create_admin(password: str, engine: "Engine") -> None:
    local_session_maker = build_local_session_maker(engine)

    with local_session_maker() as db:
        _ = signup_user(db, name="admin", first_name="admin", last_name="admin", password=password)


class MissingPhaseDuringInitError(Exception):
    def __init__(self, phase_code: str) -> None:
        super().__init__(
            f"Error during database initialization: phase_code={phase_code} not found."
        )


class MissingTeamDuringInitError(Exception):
    def __init__(self, team_code: str) -> None:
        super().__init__(f"Error during database initialization: team_code={team_code} not found.")


def initialize_database(engine: "Engine", app: "FastAPI") -> None:
    local_session_maker = build_local_session_maker(engine)

    with local_session_maker() as db:
        data_folder = get_settings().data_folder

        phases = json.loads(Path(data_folder, "phases.json").read_text(encoding="utf-8"))

        db.add_all(PhaseModel(**phase) for phase in phases)
        db.flush()

        groups = json.loads(Path(data_folder, "groups.json").read_text(encoding="utf-8"))

        for group in groups:
            phase_code = group.pop("phase_code")

            phase = db.query(PhaseModel).filter_by(code=phase_code).first()

            if phase is None:
                raise MissingPhaseDuringInitError(phase_code)

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

                if team1 is None:
                    raise MissingTeamDuringInitError(team1_code)

                match["team1_id"] = team1.id

            if team2_code is None:
                match["team2_id"] = None
            else:
                team2 = db.query(TeamModel).filter_by(code=team2_code).first()

                if team2 is None:
                    raise MissingTeamDuringInitError(team2_code)

                match["team2_id"] = team2.id

            group = db.query(GroupModel).filter_by(code=match.pop("group_code")).first()
            match["group_id"] = group.id

        db.add_all(MatchReferenceModel(**match) for match in matches)
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


class ComputePointsRuleNotDefinedError(Exception):
    def __init__(self) -> None:
        super().__init__("Compute points rule is not defined.")


def compute_score_board(engine: "Engine") -> None:
    local_session_maker = build_local_session_maker(engine)

    with local_session_maker() as db:
        admin = db.query(UserModel).filter_by(name="admin").first()

        if admin is None:
            raise NoAdminUser

        rule_config = get_settings().rules.compute_points

        if rule_config is None:
            raise ComputePointsRuleNotDefinedError

        compute_points_func(db, admin, rule_config)
