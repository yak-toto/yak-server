import secrets
import string
from datetime import datetime

from dateutil import tz


def get_random_string(length: int) -> str:
    return "".join(secrets.choice(string.ascii_letters) for _ in range(length))


def get_paris_datetime_now() -> datetime:
    return datetime.now(tz=tz.gettz("Europe/Paris"))
