from typing import TYPE_CHECKING

import pytest

from testing.mock import MockSettings
from yak_server import create_app
from yak_server.cli.database import (
    MissingGroupDuringInitError,
    MissingPhaseDuringInitError,
    MissingTeamDuringInitError,
    initialize_database,
)

if TYPE_CHECKING:
    from sqlalchemy import Engine


def test_missing_phase(monkeypatch: pytest.MonkeyPatch, engine_for_test: "Engine") -> None:
    monkeypatch.setattr(
        "yak_server.cli.database.get_settings",
        MockSettings(data_folder_relative="test_missing_phase"),
    )

    app = create_app()

    with pytest.raises(MissingPhaseDuringInitError) as exception:
        initialize_database(engine_for_test, app)

    assert (
        str(exception.value) == "Error during database initialization: phase_code=GROUP not found."
    )


def test_missing_team1(monkeypatch: pytest.MonkeyPatch, engine_for_test: "Engine") -> None:
    monkeypatch.setattr(
        "yak_server.cli.database.get_settings",
        MockSettings(data_folder_relative="test_missing_team1"),
    )

    app = create_app()

    with pytest.raises(MissingTeamDuringInitError) as exception:
        initialize_database(engine_for_test, app)

    assert str(exception.value) == "Error during database initialization: team_code=AD not found."


def test_missing_team2(monkeypatch: pytest.MonkeyPatch, engine_for_test: "Engine") -> None:
    monkeypatch.setattr(
        "yak_server.cli.database.get_settings",
        MockSettings(data_folder_relative="test_missing_team2"),
    )

    app = create_app()

    with pytest.raises(MissingTeamDuringInitError) as exception:
        initialize_database(engine_for_test, app)

    assert str(exception.value) == "Error during database initialization: team_code=BR not found."


def test_missing_group(monkeypatch: pytest.MonkeyPatch, engine_for_test: "Engine") -> None:
    monkeypatch.setattr(
        "yak_server.cli.database.get_settings",
        MockSettings(data_folder_relative="test_missing_group"),
    )

    app = create_app()

    with pytest.raises(MissingGroupDuringInitError) as exception:
        initialize_database(engine_for_test, app)

    assert str(exception.value) == "Error during database initialization: group_code=A not found."
