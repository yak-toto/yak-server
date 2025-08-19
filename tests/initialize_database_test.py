from typing import TYPE_CHECKING

import pytest

from testing.util import get_resources_path
from yak_server import create_app
from yak_server.cli.database import (
    MissingGroupDuringInitError,
    MissingPhaseDuringInitError,
    MissingTeamDuringInitError,
    initialize_competition,
)

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


def test_missing_phase(db_session: "Session") -> None:
    app = create_app()

    with pytest.raises(MissingPhaseDuringInitError) as exception:
        initialize_competition(db_session, app, get_resources_path("test_missing_phase"))

    assert (
        str(exception.value) == "Error during database initialization: phase_code=GROUP not found."
    )


def test_missing_team1(db_session: "Session") -> None:
    app = create_app()

    with pytest.raises(MissingTeamDuringInitError) as exception:
        initialize_competition(db_session, app, get_resources_path("test_missing_team1"))

    assert str(exception.value) == "Error during database initialization: team_code=AD not found."


def test_missing_team2(db_session: "Session") -> None:
    app = create_app()

    with pytest.raises(MissingTeamDuringInitError) as exception:
        initialize_competition(db_session, app, get_resources_path("test_missing_team2"))

    assert str(exception.value) == "Error during database initialization: team_code=BR not found."


def test_missing_group(db_session: "Session") -> None:
    app = create_app()

    with pytest.raises(MissingGroupDuringInitError) as exception:
        initialize_competition(db_session, app, get_resources_path("test_missing_group"))

    assert str(exception.value) == "Error during database initialization: group_code=A not found."
