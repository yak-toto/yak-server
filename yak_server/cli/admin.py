from typing import TYPE_CHECKING

import click

from yak_server.database.models import Role
from yak_server.database.session import build_local_session_maker
from yak_server.helpers.authentication import NameAlreadyExistsError, signup_user

if TYPE_CHECKING:
    from sqlalchemy import Engine


def create_admin(password: str, engine: "Engine") -> None:
    local_session_maker = build_local_session_maker(engine)

    with local_session_maker() as db:
        try:
            _ = signup_user(
                db,
                name="admin",
                first_name="admin",
                last_name="admin",
                password=password,
                role=Role.ADMIN,
            )
        except NameAlreadyExistsError:
            click.echo("Admin already exists")
