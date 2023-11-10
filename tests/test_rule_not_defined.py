import json
from pathlib import Path
from secrets import randbelow
from uuid import uuid4

import pytest
from typer.testing import CliRunner

from yak_server.cli import app
from yak_server.cli.env import RuleNotDefinedError

from .utils import get_random_string

runner = CliRunner()


def test_rule_not_defined(monkeypatch: pytest.MonkeyPatch) -> None:
    with runner.isolated_filesystem():
        competion_dir = Path("data") / "fake_competition"

        rules_dir = competion_dir / "rules"
        rules_dir.mkdir(parents=True)

        rule_id = uuid4()

        with (rules_dir / f"{rule_id}.json").open(mode="w") as file:
            file.write(json.dumps({}))

        with (competion_dir / "config.ini").open(mode="w") as file:
            file.write("[locking]\ndatetime = 2022-11-20T17:00:00.000000+01:00\n")

        monkeypatch.setattr("yak_server.cli.env.__file__", Path("cli") / "env.py")

        user_name = get_random_string(6)
        password = get_random_string(100)
        port = randbelow(10000)
        database = get_random_string(20)

        result = runner.invoke(
            app,
            ["env", "init"],
            input=f"y\ny\n{user_name}\n{password}\n{port}\n{database}\n1800\n1\n",
        )

        assert result.exit_code == 1
        assert result.exception is not None
        assert isinstance(result.exception, RuleNotDefinedError)
        assert str(result.exception) == f"Rule not defined: {rule_id}"
