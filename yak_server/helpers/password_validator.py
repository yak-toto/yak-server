import re
from dataclasses import dataclass


@dataclass(init=False, eq=False, frozen=True)
class PasswordRequirements:
    MINIMUM_LENGTH: int = 8
    UPPERCASE: bool = True
    LOWERCASE: bool = True
    DIGIT: bool = True
    NO_SPACE: bool = True


class PasswordRequirementsError(Exception):
    pass


class TooShortError(PasswordRequirementsError):
    def __init__(self, minimum_length: int) -> None:
        super().__init__(f"Password is too short. Minimum size is {minimum_length}.")


class NoUpperCaseError(PasswordRequirementsError):
    def __init__(self) -> None:
        super().__init__("At least one upper-case letter expected.")


class NoLowerCaseError(PasswordRequirementsError):
    def __init__(self) -> None:
        super().__init__("At least one lower-case letter expected.")


class NoDigitError(PasswordRequirementsError):
    def __init__(self) -> None:
        super().__init__("At least one digit expected.")


class SpaceError(PasswordRequirementsError):
    def __init__(self) -> None:
        super().__init__("Password must not contain spaces.")


def validate_password(password: str) -> None:
    password_requirements = PasswordRequirements()

    if len(password) < password_requirements.MINIMUM_LENGTH:
        raise TooShortError(password_requirements.MINIMUM_LENGTH)

    if not re.search(r"[A-Z]", password) and password_requirements.UPPERCASE:
        raise NoUpperCaseError

    if not re.search(r"[a-z]", password) and password_requirements.LOWERCASE:
        raise NoLowerCaseError

    if not re.search(r"[0-9]", password) and password_requirements.DIGIT:
        raise NoDigitError

    if " " in password and password_requirements.NO_SPACE:
        raise SpaceError
