import secrets
import string
from datetime import datetime

from dateutil import tz


def get_random_string(length: int):
    return "".join(secrets.choice(string.ascii_letters) for _ in range(length))


def get_paris_datetime_now():
    return datetime.now(tz=tz.gettz("Europe/Paris"))
