import argparse
from enum import Enum

NUMBER_OF_DIGITS = 3


class ReleaseType(Enum):
    MAJOR = "major"
    MINOR = "minor"
    PATCH = "patch"


def parse_version(version: str) -> list[int]:
    parsed_version = [int(version_digit) for version_digit in version.split(".")]

    if len(parsed_version) != NUMBER_OF_DIGITS:
        msg = f"Incorrect version {parsed_version}. Expecting 3 digits."
        raise ValueError(msg)

    return parsed_version


def unparse_version(major: int, minor: int, patch: int) -> str:
    return f"{major}.{minor}.{patch}"


def compute_new_version(current_version: str, release_type: ReleaseType) -> str:
    parsed_current_version = parse_version(current_version)

    if release_type == ReleaseType.MAJOR:
        return unparse_version(parsed_current_version[0] + 1, 0, 0)

    if release_type == ReleaseType.MINOR:
        return unparse_version(parsed_current_version[0], parsed_current_version[1] + 1, 0)

    return unparse_version(
        parsed_current_version[0],
        parsed_current_version[1],
        parsed_current_version[2] + 1,
    )


if __name__ == "__main__":  # pragma: no cover
    parser = argparse.ArgumentParser()
    parser.add_argument("current_version")
    parser.add_argument("release_type", choices=[e.value for e in ReleaseType])

    args = parser.parse_args()

    print(compute_new_version(args.current_version, ReleaseType(args.release_type)))

    raise SystemExit(0)
