from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

from hatchling.builders.hooks.plugin.interface import BuildHookInterface


class CopyAlembicIniBuildHook(BuildHookInterface):
    PLUGIN_NAME = "copy-alembic-ini"

    def initialize(self, version: str, build_data: dict[str, Any]) -> None:  # noqa: ARG002
        root = Path(self.root)

        shutil.copy(root / "alembic.ini", root / "yak_server")

    def finalize(self, version: str, build_data: dict[str, Any], artifact_path: str) -> None:  # noqa: ARG002
        root = Path(self.root)

        (root / "yak_server" / "alembic.ini").unlink(missing_ok=True)
