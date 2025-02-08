import pytest

from testing.mock import MockSettings
from yak_server import create_app
from yak_server.cli.database import (
    MissingPhaseDuringInitError,
    MissingTeamDuringInitError,
    initialize_database,
)


def test_missing_phase(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "yak_server.cli.database.get_settings",
        MockSettings(data_folder_relative="test_missing_phase"),
    )

    app = create_app()

    with pytest.raises(MissingPhaseDuringInitError) as exception:
        initialize_database(app)

    assert (
        str(exception.value) == "Error during database initialization: phase_code=GROUP not found."
    )


def test_missing_team1(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "yak_server.cli.database.get_settings",
        MockSettings(data_folder_relative="test_missing_team1"),
    )

    app = create_app()

    with pytest.raises(MissingTeamDuringInitError) as exception:
        initialize_database(app)

    assert str(exception.value) == "Error during database initialization: team_code=AD not found."


def test_missing_team2(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "yak_server.cli.database.get_settings",
        MockSettings(data_folder_relative="test_missing_team2"),
    )

    app = create_app()

    with pytest.raises(MissingTeamDuringInitError) as exception:
        initialize_database(app)

    assert str(exception.value) == "Error during database initialization: team_code=BR not found."
