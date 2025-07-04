#!/usr/bin/env -S uv run --script
#
# /// script
# requires-python = ">=3.9"
# ///

import operator
import subprocess
from pathlib import Path


def main() -> int:
    competitions = sorted(
        (
            directory.stem
            for directory in (Path(__file__).parents[1] / "yak_server" / "data").iterdir()
        ),
        key=operator.itemgetter(slice(-4, None)),
    )

    yak_version = subprocess.run(
        ["uv", "version", "--short"], check=False, capture_output=True, text=True
    ).stdout.strip()

    for competition in competitions:
        command = [
            "docker",
            "buildx",
            "build",
            "--build-arg",
            f"COMPETITION={competition}",
            "-t",
            f"yak_server:{yak_version}-{competition}",
            f"{Path(__file__).parents[1].resolve()}",
        ]

        subprocess.run(command, check=False)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
