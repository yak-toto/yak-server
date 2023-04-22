import pytest

from yak_server.cli.database import (
    SyncOfficialResultsNotAvailableError,
    synchronize_official_results,
)


def test_db_sync(monkeypatch: "pytest.MonkeyPatch") -> None:
    monkeypatch.setattr("yak_server.cli.database.bs4", None)

    with pytest.raises(SyncOfficialResultsNotAvailableError) as exception:
        synchronize_official_results()

    assert (
        str(exception.value)
        == "Synchronize official results is not available without beautifulsoup4 installed. "
        "To enable it, please run: pip install beautifulsoup4[lxml]"
    )
