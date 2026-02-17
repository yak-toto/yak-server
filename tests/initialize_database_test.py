from typing import TYPE_CHECKING

import pytest

from testing.util import get_resources_path
from yak_server import create_app
from yak_server.cli.database import (
    MissingGroupDuringInitError,
    MissingPhaseDuringInitError,
    MissingTeamDuringInitError,
    delete_database,
    initialize_database,
)
from yak_server.database.models import (
    GroupModel,
    MatchReferenceModel,
    PhaseModel,
    TeamModel,
)
from yak_server.database.session import build_local_session_maker

if TYPE_CHECKING:
    from sqlalchemy import Engine


def test_missing_phase(engine_for_test: "Engine") -> None:
    app = create_app()

    with pytest.raises(MissingPhaseDuringInitError) as exception:
        initialize_database(engine_for_test, app, get_resources_path("test_missing_phase"))

    assert (
        str(exception.value) == "Error during database initialization: phase_code=GROUP not found."
    )


def test_missing_team1(engine_for_test: "Engine") -> None:
    app = create_app()

    with pytest.raises(MissingTeamDuringInitError) as exception:
        initialize_database(engine_for_test, app, get_resources_path("test_missing_team1"))

    assert str(exception.value) == "Error during database initialization: team_code=AD not found."


def test_missing_team2(engine_for_test: "Engine") -> None:
    app = create_app()

    with pytest.raises(MissingTeamDuringInitError) as exception:
        initialize_database(engine_for_test, app, get_resources_path("test_missing_team2"))

    assert str(exception.value) == "Error during database initialization: team_code=BR not found."


def test_missing_group(engine_for_test: "Engine") -> None:
    app = create_app()

    with pytest.raises(MissingGroupDuringInitError) as exception:
        initialize_database(engine_for_test, app, get_resources_path("test_missing_group"))

    assert str(exception.value) == "Error during database initialization: group_code=A not found."


def test_upsert(engine_for_test: "Engine") -> None:
    app = create_app()

    # First initialization: insert records
    delete_database(engine_for_test, debug=True)
    initialize_database(engine_for_test, app, get_resources_path("test_upsert"))

    local_session_maker = build_local_session_maker(engine_for_test)

    with local_session_maker() as db:
        phase = db.query(PhaseModel).filter_by(code="GROUP").one()
        assert phase.description_fr == "Phase de groupes"
        assert phase.description_en == "Group stage"
        assert phase.index == 1

        group = db.query(GroupModel).filter_by(code="A").one()
        assert group.description_fr == "Groupe A"
        assert group.description_en == "Group A"
        assert group.index == 1

        france = db.query(TeamModel).filter_by(code="FR").one()
        assert france.description_fr == "France"
        assert france.description_en == "France"

        brazil = db.query(TeamModel).filter_by(code="BR").one()
        assert brazil.description_fr == "Br\u00e9sil"
        assert brazil.description_en == "Brazil"

        match = db.query(MatchReferenceModel).filter_by(group_id=group.id, index=1).one()
        assert match.team1_id == france.id
        assert match.team2_id == brazil.id

    # Second initialization: upsert with updated data
    initialize_database(engine_for_test, app, get_resources_path("test_upsert_updated"))

    with local_session_maker() as db:
        # Phase should be updated
        phase = db.query(PhaseModel).filter_by(code="GROUP").one()
        assert phase.description_fr == "Phases de poules"
        assert phase.description_en == "Group phase"
        assert phase.index == 1

        # Group should be updated
        group = db.query(GroupModel).filter_by(code="A").one()
        assert group.description_fr == "Poule A"
        assert group.description_en == "Pool A"
        assert group.index == 1

        # Teams should be updated
        france = db.query(TeamModel).filter_by(code="FR").one()
        assert france.description_fr == "Les Bleus"
        assert france.description_en == "The Blues"

        brazil = db.query(TeamModel).filter_by(code="BR").one()
        assert brazil.description_fr == "Sele\u00e7\u00e3o"
        assert brazil.description_en == "The Selection"

        # Match teams should be swapped
        match = db.query(MatchReferenceModel).filter_by(group_id=group.id, index=1).one()
        assert match.team1_id == brazil.id
        assert match.team2_id == france.id

    # Cleanup
    delete_database(engine_for_test, debug=True)
