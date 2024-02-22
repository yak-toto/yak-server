import pytest

from yak_server.cli.database.sync import (
    SyncOfficialResultsNotAvailableError,
    synchronize_official_results,
)


def test_db_sync(monkeypatch: "pytest.MonkeyPatch") -> None:
    monkeypatch.setattr("yak_server.cli.database.sync.bs4", None)

    with pytest.raises(SyncOfficialResultsNotAvailableError) as exception:
        synchronize_official_results()

    assert str(exception.value) == (
        "Synchronize official results is not available without sync extra dependency installed. "
        "To enable it, please run: pip install yak-server[sync]"
    )
