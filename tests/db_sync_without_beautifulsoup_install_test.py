from typing import TYPE_CHECKING

import pytest

from yak_server.cli.database.sync import (
    SyncOfficialResultsNotAvailableError,
    synchronize_official_results,
)

if TYPE_CHECKING:
    from sqlalchemy import Engine


def test_db_sync(monkeypatch: "pytest.MonkeyPatch", engine_for_test: "Engine") -> None:
    monkeypatch.setattr("yak_server.cli.database.sync.bs4", None)

    with pytest.raises(SyncOfficialResultsNotAvailableError) as exception:
        synchronize_official_results(engine_for_test)

    assert str(exception.value) == (
        "Synchronize official results is not available without sync extra dependency installed. "
        "To enable it, please run: uv pip install yak-server[sync]"
    )
