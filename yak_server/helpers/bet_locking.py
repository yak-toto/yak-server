from datetime import UTC, datetime

from yak_server.database.models import UserModel

from .authentication import Permission, has_permission


def is_locked(user: UserModel, lock_datetime: datetime) -> bool:
    return not has_permission(user, Permission.ADMIN) and datetime.now(UTC) > lock_datetime
