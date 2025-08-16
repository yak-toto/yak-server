import json
import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional
from uuid import UUID

import pendulum
from sqlalchemy import update
from sqlalchemy.dialects.postgresql import insert

from yak_server.database import build_local_session_maker
from yak_server.database.models import (
    Base,
    BinaryBetModel,
    CompetitionModel,
    GroupModel,
    GroupPositionModel,
    MatchModel,
    MatchReferenceModel,
    PhaseModel,
    Role,
    ScoreBetModel,
    TeamModel,
    UserModel,
)
from yak_server.helpers.authentication import NameAlreadyExistsError, signup_user
from yak_server.helpers.rules import RULE_MAPPING, Rules
from yak_server.helpers.rules.compute_points import compute_points as compute_points_func
from yak_server.helpers.settings import get_competition, get_settings
from yak_server.v1.helpers.errors import NoAdminUser

try:
    import alembic
except ImportError:  # pragma: no cover
    # Very common pattern for optional dependency imports
    alembic = None  # type: ignore[assignment]

if TYPE_CHECKING:
    from fastapi import FastAPI
    from sqlalchemy import Engine
    from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class RecordDeletionInProductionError(Exception):
    def __init__(self) -> None:
        super().__init__("Trying to delete records in production using script. DO NOT DO IT.")


class TableDropInProductionError(Exception):
    def __init__(self) -> None:
        super().__init__("Trying to drop database tables in production using script. DO NOT DO IT.")


class RuleNotDefinedError(Exception):
    def __init__(self, rule_id: UUID) -> None:
        super().__init__(f"Rule not defined: {rule_id}")


def create_database(engine: "Engine") -> None:
    Base.metadata.create_all(bind=engine)


def create_admin(password: str, engine: "Engine") -> None:
    local_session_maker = build_local_session_maker(engine)

    with local_session_maker() as db:
        competition = get_competition(db, get_settings())

        try:
            _ = signup_user(
                db,
                name="admin",
                first_name="admin",
                last_name="admin",
                password=password,
                role=Role.ADMIN,
                competition=competition,
            )
        except NameAlreadyExistsError:
            print("Admin already exists")


class MissingPhaseDuringInitError(Exception):
    def __init__(self, phase_code: str) -> None:
        super().__init__(
            f"Error during database initialization: phase_code={phase_code} not found."
        )


class MissingTeamDuringInitError(Exception):
    def __init__(self, team_code: str) -> None:
        super().__init__(f"Error during database initialization: team_code={team_code} not found.")


class MissingGroupDuringInitError(Exception):
    def __init__(self, group_code: str) -> None:
        super().__init__(
            f"Error during database initialization: group_code={group_code} not found."
        )


def fetch_team_id(team_code: Optional[str], db: "Session") -> Optional[UUID]:
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


def store_competition_data(db: "Session", data_folder: Path) -> CompetitionModel:
    common_settings = json.loads((data_folder / "common.json").read_text())

    lock_datetime = pendulum.parse(common_settings["lock_datetime"], exact=True)
    official_results_url = common_settings["official_results_url"]
    description_fr = common_settings["description"]["fr"]
    description_en = common_settings["description"]["en"]

    # Load rules in environment
    rules_list: dict[str, Any] = {}

    for rule_file in Path(data_folder, "rules").glob("*.json"):
        rule_id = UUID(rule_file.stem)

        if rule_id not in RULE_MAPPING:
            raise RuleNotDefinedError(rule_id)

        rule_name = RULE_MAPPING[rule_id].attribute

        rules_list[rule_name] = json.loads(rule_file.read_text())

    rules = Rules.model_validate(rules_list)

    competition = CompetitionModel(
        name=data_folder.stem,
        description_fr=description_fr,
        description_en=description_en,
        lock_datetime=lock_datetime,
        official_results_url=official_results_url,
        rules=rules.model_dump(exclude_unset=True),
    )

    db.add(competition)

    db.flush()

    return competition


def get_data_folder() -> Path:
    return Path(__file__).parents[2] / "data"


def initialize_competition(db: "Session", app: "FastAPI", data_folder: Path) -> None:
    competition = store_competition_data(db, data_folder)

    db.flush()

    phases = json.loads(Path(data_folder, "phases.json").read_text(encoding="utf-8"))

    for phase in phases:
        db.execute(
            insert(PhaseModel).values(**phase).on_conflict_do_nothing(index_elements=["code"])
        )

    db.flush()

    groups = json.loads(Path(data_folder, "groups.json").read_text(encoding="utf-8"))

    for group in groups:
        phase_code = group.pop("phase_code")

        phase = db.query(PhaseModel).filter_by(code=phase_code).first()

        if phase is None:
            raise MissingPhaseDuringInitError(phase_code)

        group["phase_id"] = phase.id

    for group in groups:
        db.execute(
            insert(GroupModel).values(**group).on_conflict_do_nothing(index_elements=["code"])
        )

    db.flush()

    teams = json.loads(Path(data_folder, "teams.json").read_text(encoding="utf-8"))

    for team in teams:
        team["flag_url"] = ""

        db.execute(insert(TeamModel).values(**team).on_conflict_do_nothing(index_elements=["code"]))

        db.flush()

        team_instance = db.query(TeamModel).filter_by(code=team["code"]).first()

        if team_instance is None:  # pragma: no cover
            raise MissingTeamDuringInitError(team_code=team["code"])

        update_flag_url_stmt = (
            update(TeamModel)
            .where(TeamModel.code == team["code"])
            .values(flag_url=app.url_path_for("retrieve_team_flag_by_id", team_id=team_instance.id))
        )

        db.execute(update_flag_url_stmt)
        db.flush()

    matches = json.loads(Path(data_folder, "matches.json").read_text(encoding="utf-8"))

    for match in matches:
        match["team1_id"] = fetch_team_id(match.pop("team1_code"), db)
        match["team2_id"] = fetch_team_id(match.pop("team2_code"), db)
        match["group_id"] = fetch_group_id(match.pop("group_code"), db)
        match["competition_id"] = competition.id

    for match in matches:
        db.execute(
            insert(MatchReferenceModel)
            .values(**match)
            .on_conflict_do_nothing(index_elements=["group_id", "index", "competition_id"])
        )

    db.commit()


def initialize_database(engine: "Engine", app: "FastAPI") -> None:
    local_session_maker = build_local_session_maker(engine)

    for data_folder in get_data_folder().iterdir():
        with local_session_maker() as db:
            initialize_competition(db, app, data_folder)


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
        db.query(CompetitionModel).delete()
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

        competition = get_competition(db, get_settings())

        if competition is None:
            raise ValueError

        rule_config = Rules.model_validate(competition.rules).compute_points

        if rule_config is None:
            raise ComputePointsRuleNotDefinedError

        compute_points_func(db, admin, rule_config)
