import json
from pathlib import Path
from secrets import randbelow
from uuid import uuid4

import pytest
from click.testing import CliRunner

from testing.util import get_random_string
from yak_server.cli import app
from yak_server.cli.env import RuleNotDefinedError

runner = CliRunner()


def test_rule_not_defined(monkeypatch: pytest.MonkeyPatch) -> None:
    with runner.isolated_filesystem():
        competition_dir = Path("data", "fake_competition")

        rules_dir = competition_dir / "rules"
        rules_dir.mkdir(parents=True)

        rule_id = uuid4()

        (rules_dir / f"{rule_id}.json").write_text(json.dumps({}))

        (competition_dir / "config.ini").write_text(
            "[locking]\ndatetime = 2022-11-20T17:00:00.000000+01:00\n"
        )

        monkeypatch.setattr("yak_server.cli.env.__file__", Path("cli", "env.py"))

        host = get_random_string(20)
        user_name = get_random_string(6)
        password = get_random_string(100)
        port = randbelow(10000)
        database = get_random_string(20)

        result = runner.invoke(
            app,
            ["env", "all"],
            input=f"y\n{host}\n{user_name}\n{password}\n{port}\n{database}\n1800\n1800\nfake_competition\n",
        )

        assert result.exit_code == 1
        assert result.exception is not None
        assert isinstance(result.exception, RuleNotDefinedError)
        assert str(result.exception) == f"Rule not defined: {rule_id}"
