import argparse
from enum import Enum
from typing import List, Tuple

from yak_server import __version__


class ReleaseType(Enum):
    major = "major"
    minor = "minor"
    patch = "patch"


def parse_version(version: str) -> List[int]:
    return [int(version_digit) for version_digit in version.split(".")]


def unparse_version(major: int, minor: int, patch: int) -> str:
    return f"{major}.{minor}.{patch}"


def compute_new_version(current_version: str, release_type: ReleaseType) -> Tuple[int, int, int]:
    current_version = parse_version(__version__)

    if release_type == ReleaseType.major:
        return unparse_version(current_version[0] + 1, 0, 0)

    if release_type == ReleaseType.minor:
        return unparse_version(current_version[0], current_version[1] + 1, 0)

    if release_type == ReleaseType.patch:
        return unparse_version(current_version[0], current_version[1], current_version[2] + 1)

    return ValueError(f"Invalid release type: {release_type}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("release_type")

    args = parser.parse_args()

    print(compute_new_version(__version__, ReleaseType(args.release_type)))

    raise SystemExit(0)
