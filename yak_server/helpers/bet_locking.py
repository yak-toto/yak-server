import pendulum

from yak_server.database.models import UserModel

from .authentication import Permission, has_permission


def is_locked(user: UserModel, lock_datetime: pendulum.DateTime) -> bool:
    return not has_permission(user, Permission.ADMIN) and pendulum.now("UTC") > lock_datetime
