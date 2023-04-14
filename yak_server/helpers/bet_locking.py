from datetime import datetime, timezone


def is_locked(user_name: str, lock_datetime: datetime) -> bool:
    return user_name != "admin" and datetime.now(tz=timezone.utc) > lock_datetime
