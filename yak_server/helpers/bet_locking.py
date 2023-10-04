import pendulum


def is_locked(user_name: str, lock_datetime: pendulum.DateTime) -> bool:
    return user_name != "admin" and pendulum.now("UTC") > lock_datetime
