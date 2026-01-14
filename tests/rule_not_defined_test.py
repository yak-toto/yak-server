import json
from pathlib import Path
from uuid import uuid4

import pytest
from click.testing import CliRunner

from yak_server.cli.database import RuleNotDefinedError, load_rules

runner = CliRunner()


def test_rule_not_defined() -> None:
    with runner.isolated_filesystem():
        competition_dir = Path("data", "fake_competition")

        rules_dir = competition_dir / "rules"
        rules_dir.mkdir(parents=True)

        rule_id = uuid4()

        (rules_dir / f"{rule_id}.json").write_text(json.dumps({}))

        with pytest.raises(RuleNotDefinedError) as exception:
            load_rules(competition_dir)

        assert str(exception.value) == f"Rule not defined: {rule_id}"
