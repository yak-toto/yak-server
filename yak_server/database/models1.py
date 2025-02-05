import asyncio

from argon2 import PasswordHasher
from argon2.exceptions import VerificationError
from piccolo.columns import UUID, Varchar
from piccolo.engine.postgres import PostgresEngine
from piccolo.table import Table

from . import get_postgres_settings

ph = PasswordHasher()


db_settings = get_postgres_settings()

DB = PostgresEngine(
    config={
        "host": db_settings.host,
        "user": db_settings.user_name,
        "password": db_settings.password,
        "database": db_settings.db,
        "port": db_settings.port,
    }
)


class User(Table, db=DB):
    id = UUID(primary_key=True, null=False)
    name = Varchar(100, unique=True, null=False)
    first_name = Varchar(100, null=False)
    last_name = Varchar(100, null=False)

    password = Varchar(100, null=False)
    number_match_guess = Varchar(100, null=False, default=0)
    number_score_guess = Varchar(100, null=False, default=0)
    number_qualified_teams_guess = Varchar(100, null=False, default=0)
    number_first_qualified_guess = Varchar(100, null=False, default=0)
    number_quarter_final_guess = Varchar(100, null=False, default=0)
    number_semi_final_guess = Varchar(100, null=False, default=0)
    number_final_guess = Varchar(100, null=False, default=0)
    number_winner_guess = Varchar(100, null=False, default=0)
    points = Varchar(100, null=False, default=0)

    def __init__(self, name: str, first_name: str, last_name: str, password: str) -> None:
        self.name = name
        self.first_name = first_name
        self.last_name = last_name
        self.password = ph.hash(password)

    @classmethod
    async def authenticate(cls, name: str, password: str) -> "User":
        user = await cls.select(name=name).first()

        is_correct_username = bool(user)

        try:
            if is_correct_username:
                ph.verify(user["password"], password)
            else:
                # verify password with itself to avoid timing attack
                ph.verify(ph.hash(password), password)
            is_correct_password = True
        except VerificationError:
            is_correct_password = False

        return user if is_correct_username and is_correct_password else None


async def _main() -> None:
    await User.create_table()


if __name__ == "__main__":
    asyncio.run(_main())
