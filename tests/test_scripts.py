import re

import pytest

from scripts.compute_new_version import ReleaseType, compute_new_version


def test_compute_new_version() -> None:
    assert compute_new_version("1.30.2", ReleaseType.MAJOR) == "2.0.0"


def test_compute_new_minor_version() -> None:
    assert compute_new_version("0.5.3", ReleaseType.MINOR) == "0.6.0"


def test_compute_new_patch_version() -> None:
    assert compute_new_version("5.4.1", ReleaseType.PATCH) == "5.4.2"


def test_compute_incorrect_version() -> None:
    major, minor = 1, 3

    with pytest.raises(
        ValueError,
        match=re.escape(f"Incorrect version [{major}, {minor}]. Expecting 3 digits."),
    ):
        compute_new_version(f"{major}.{minor}", ReleaseType.MAJOR)


def test_compute_value_error() -> None:
    major, minor, patch = "a", 3, 6

    with pytest.raises(
        ValueError,
        match=re.escape(f"invalid literal for int() with base 10: '{major}'"),
    ):
        compute_new_version(f"{major}.{minor}.{patch}", ReleaseType.PATCH)
