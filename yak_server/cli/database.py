import json
import logging
import subprocess
import warnings
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, List, Optional, Tuple

import httpx
import pendulum
from sqlalchemy import and_

from yak_server.database import Base, SessionLocal, engine, mysql_settings
from yak_server.database.models import (
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
from yak_server.helpers.logging import setup_logging
from yak_server.helpers.rules.compute_points import compute_points as compute_points_func
from yak_server.helpers.settings import get_settings
from yak_server.v1.models.users import SignupIn
from yak_server.v1.routers.users import signup_user

try:
    import alembic
except ImportError:  # pragma: no cover
    alembic = None  # type: ignore[assignment]

try:
    import bs4
except ImportError:  # pragma: no cover
    bs4 = None  # type: ignore[assignment]

try:
    import lxml
except ImportError:  # pragma: no cover
    lxml = None  # type: ignore[assignment]


if TYPE_CHECKING:
    from fastapi import FastAPI

logger = logging.getLogger(__name__)


class RecordDeletionInProductionError(Exception):
    def __init__(self) -> None:
        super().__init__("Trying to delete records in production using script. DO NOT DO IT.")


class TableDropInProductionError(Exception):
    def __init__(self) -> None:
        super().__init__("Trying to drop database tables in production using script. DO NOT DO IT.")


class BackupError(Exception):
    def __init__(self, description: str) -> None:
        super().__init__(f"Error during backup. {description}")


def create_database() -> None:
    with SessionLocal():
        Base.metadata.create_all(bind=engine)


def create_admin(password: str) -> None:
    with SessionLocal() as db:
        _ = signup_user(
            db,
            SignupIn(name="admin", first_name="admin", last_name="admin", password=password),
        )


def initialize_database(app: "FastAPI") -> None:
    with SessionLocal() as db:
        data_folder = get_settings().data_folder

        phases = json.loads(Path(data_folder, "phases.json").read_text())

        db.add_all(PhaseModel(**phase) for phase in phases)
        db.flush()

        groups = json.loads(Path(data_folder, "groups.json").read_text())

        for group in groups:
            phase = db.query(PhaseModel).filter_by(code=group.pop("phase_code")).first()
            group["phase_id"] = phase.id

        db.add_all(GroupModel(**group) for group in groups)
        db.flush()

        teams = json.loads(Path(data_folder, "teams.json").read_text())

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

        matches = json.loads(Path(data_folder, "matches.json").read_text())

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


def backup_database() -> None:
    setup_logging(debug=False)

    result = subprocess.run(
        [  # noqa: S603, S607
            "mysqldump",
            mysql_settings.db,
            "-u",
            mysql_settings.user_name,
            "-P",
            str(mysql_settings.port),
            "--protocol=tcp",
            f"--password={mysql_settings.password}",
        ],
        capture_output=True,
        encoding="utf-8",
        check=False,
    )

    backup_datetime = pendulum.now("UTC")

    if result.returncode:
        error_message = (
            f"Something went wrong when backup on {backup_datetime}: "
            f"{result.stderr.replace(mysql_settings.password, '********')}"
        )

        logger.error(error_message)

        raise BackupError(error_message)

    backup_location = Path(__file__).parent / "backup_files"
    backup_location.mkdir(exist_ok=True)

    file_path = (
        backup_location / f"yak_toto_backup_{backup_datetime.format('YYYYMMDD[T]HHmmssZZ')}.sql"
    )

    file_path.write_text(result.stdout)
    logger.info(f"Backup done on {backup_datetime}")


def delete_database(app: "FastAPI") -> None:
    if not app.debug:
        raise RecordDeletionInProductionError

    with SessionLocal() as db:
        db.query(GroupPositionModel).delete()
        db.query(ScoreBetModel).delete()
        db.query(BinaryBetModel).delete()
        db.query(UserModel).delete()
        db.query(MatchReferenceModel).delete()
        db.query(MatchModel).delete()
        db.query(GroupModel).delete()
        db.query(PhaseModel).delete()
        db.query(TeamModel).delete()
        db.commit()


def drop_database(app: "FastAPI") -> None:
    if not app.debug:
        raise TableDropInProductionError

    with SessionLocal():
        Base.metadata.drop_all(bind=engine)


def setup_migration() -> None:
    alembic_ini_path = Path(__file__).parents[2] / "alembic.ini"

    print(
        "To be able to run the database migration scripts, you need to run the following command:",
    )
    print(f"export ALEMBIC_CONFIG='{alembic_ini_path.resolve()}'")
    print()
    print(
        "Follow this link for more informations: "
        "https://alembic.sqlalchemy.org/en/latest/tutorial.html#editing-the-ini-file",
    )

    if alembic is None:
        print()
        print("To enable migration using alembic, please run: pip install alembic")


def compute_score_board() -> None:
    with SessionLocal() as db:
        admin = db.query(UserModel).filter_by(name="admin").first()

        rule_config = get_settings().rules.compute_points

        compute_points_func(db, admin, rule_config)


def parse_score(content: str) -> Tuple[int, int]:
    try:
        scores = next(next(content.children).children)
    except AttributeError:
        return None, None

    try:
        score1_str, score2_str = scores.split("\u2013")
    except ValueError:  # pragma: no cover
        return None, None

    try:
        score1 = int(score1_str)
    except ValueError:  # pragma: no cover
        warnings.warn(f"Couldn't parse score1: '{score1_str}'", stacklevel=2)
        score1 = None

    try:
        score2 = int(score2_str)
    except ValueError:  # pragma: no cover
        warnings.warn(f"Couldn't parse score2: '{score2_str}'", stacklevel=2)
        score2 = None

    return score1, score2


def parse_penalty(content: str) -> bool:
    penalties_tag = content.find("a", string="Penalties")
    score_content = penalties_tag.next.parent.find_next("th").string

    score1, score2 = score_content.split("\u2013")

    return int(score1) > int(score2)


def is_penalties(content: str) -> bool:
    return bool(content.find("a", string="Penalties"))


class SyncOfficialResultsNotAvailableError(Exception):
    def __init__(self) -> None:
        super().__init__(
            "Synchronize official results is not available without beautifulsoup4 installed. "
            "To enable it, please run: pip install beautifulsoup4[lxml]"
        )


@dataclass
class GroupContainer:
    model: GroupModel
    content: str


@dataclass
class Group:
    index: int


@dataclass
class Team:
    score: int
    description: str
    won: Optional[bool] = None


@dataclass
class Match:
    index: int
    group: Group
    team1: Team
    team2: Team


def extract_matches_from_html(groups: List[GroupContainer]) -> List[Match]:
    matches = []

    for index, group in enumerate(groups, start=1):
        try:
            next_group = groups[index + 1]
        except IndexError:
            next_group = None

        previous_matches_html = (
            frozenset(next_group.content.find_all_previous("div", class_="footballbox"))
            if next_group is not None
            else None
        )

        next_matches_html = group.content.find_all_next("div", class_="footballbox")

        matches_html = [
            match
            for match in next_matches_html
            if previous_matches_html is None or match in previous_matches_html
        ]

        for match_index, match_html in enumerate(matches_html, start=1):
            score1, score2 = parse_score(match_html.find("th", class_="fscore"))

            match = Match(
                index=match_index,
                group=Group(index=group.model.index),
                team1=Team(
                    description=(
                        match_html.find("th", class_="fhome").get_text().replace("\xa0", "")
                    ),
                    score=score1,
                ),
                team2=Team(
                    description=(
                        match_html.find("th", class_="faway").get_text().replace("\xa0", "")
                    ),
                    score=score2,
                ),
            )

            if is_penalties(match_html):
                is_one_won = parse_penalty(match_html)

                match.team1.won = is_one_won
                match.team2.won = not is_one_won

            matches.append(match)

    return matches


def synchronize_official_results() -> None:
    if bs4 is None or lxml is None:
        raise SyncOfficialResultsNotAvailableError

    official_results_url = get_settings().official_results_url

    response = httpx.get(str(official_results_url))

    soup = bs4.BeautifulSoup(response.text, "lxml")

    db = SessionLocal()

    groups = [
        GroupContainer(model=group, content=content.parent.parent)
        for group in db.query(GroupModel).order_by(GroupModel.index)
        for content in soup.find("span", string=group.description_en, class_="mw-headline")
    ]

    matches = extract_matches_from_html(groups)

    admin = db.query(UserModel).filter_by(name="admin").first()

    for match in matches:
        score_bet = (
            admin.score_bets.join(ScoreBetModel.match)
            .join(MatchModel.group)
            .filter(and_(GroupModel.index == match.group.index, MatchModel.index == match.index))
            .first()
        )

        if score_bet is not None:
            score_bet.score1 = match.team1.score
            score_bet.score2 = match.team2.score

        binary_bet = (
            admin.binary_bets.join(BinaryBetModel.match)
            .join(MatchModel.group)
            .join(GroupModel.phase)
            .filter(and_(GroupModel.index == match.group.index, MatchModel.index == match.index))
            .first()
        )

        if binary_bet is not None:
            team1 = db.query(TeamModel).filter_by(description_en=match.team1.description).first()
            team2 = db.query(TeamModel).filter_by(description_en=match.team2.description).first()

            if team1 is not None and team2 is not None:
                binary_bet.match.team1_id = team1.id
                binary_bet.match.team2_id = team2.id

                if match.team1.won is not None:
                    binary_bet.is_one_won = match.team1.won
                else:
                    binary_bet.is_one_won = match.team1.score > match.team2.score

    db.commit()
