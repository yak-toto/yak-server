import typer

from yak_server import create_app

from .database import (
    backup_database,
    create_admin,
    create_database,
    delete_database,
    drop_database,
    initialize_database,
    setup_migration,
)
from .env import init_env

app = typer.Typer()


def make_db_app() -> typer.Typer:
    db_app = typer.Typer()

    @db_app.command()
    def create() -> None:
        """Create all database tables."""
        create_database()

    @db_app.command()
    def init() -> None:
        """Initialize database."""
        app = create_app()
        initialize_database(app)

    @db_app.command()
    def drop() -> None:
        """Drop all tables."""
        app = create_app()
        drop_database(app)

    @db_app.command()
    def delete() -> None:
        """Delete all records."""
        app = create_app()
        delete_database(app)

    @db_app.command()
    def admin(
        password: str = typer.Option(..., prompt=True, confirmation_prompt=True, hide_input=True),
    ) -> None:
        """Create admin account in database."""
        create_admin(password)

    @db_app.command()
    def backup() -> None:
        """Backup database in a sql file."""
        backup_database()

    @db_app.command()
    def migration() -> None:
        """Help to run database migration scripts."""
        setup_migration()

    return db_app


def make_env_typer() -> typer.Typer:
    env_typer = typer.Typer()

    @env_typer.command()
    def init() -> None:
        """Build the env files you need to start the server."""
        init_env()

    return env_typer


app.add_typer(make_db_app(), name="db")
app.add_typer(make_env_typer(), name="env")


if __name__ == "__main__":  # pragma: no cover
    app()
