#!/usr/bin/env -S uv run --script
#
# /// script
# requires-python = ">=3.9"
# ///

import operator
import subprocess
from datetime import datetime, timezone
from pathlib import Path


def now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


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
        process = subprocess.Popen(
            [
                "docker",
                "buildx",
                "build",
                "--build-arg",
                f"COMPETITION={competition}",
                "-t",
                f"yak_server:{yak_version}-{competition}",
                f"{Path(__file__).parents[1].resolve()}",
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )

        for line in process.stdout:
            print(line, end="")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
