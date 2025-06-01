import json
from typing import Annotated

import typer

from yak_server import create_app
from yak_server.database import build_engine

from .database import (
    compute_score_board,
    create_admin,
    create_database,
    delete_database,
    drop_database,
    initialize_database,
    setup_migration,
)
from .database.sync import synchronize_official_results
from .env import init_env

app = typer.Typer()


def make_db_app() -> typer.Typer:
    db_app = typer.Typer()

    @db_app.command()
    def create() -> None:
        """Create all database tables."""
        engine = build_engine()
        create_database(engine)

    @db_app.command()
    def init() -> None:
        """Initialize database."""
        app = create_app()
        engine = build_engine()
        initialize_database(engine, app)

    @db_app.command()
    def drop() -> None:
        """Drop all tables."""
        app = create_app()
        engine = build_engine()
        drop_database(engine, debug=app.debug)

    @db_app.command()
    def delete() -> None:
        """Delete all records."""
        app = create_app()
        engine = build_engine()
        delete_database(engine, debug=app.debug)

    @db_app.command()
    def admin(
        password: str = typer.Option(..., prompt=True, confirmation_prompt=True, hide_input=True),
    ) -> None:
        """Create admin account in database."""
        engine = build_engine()
        create_admin(password, engine)

    @db_app.command()
    def migration(*, short: Annotated[bool, typer.Option("--short", "-s")] = False) -> None:
        """Help to run database migration scripts."""
        setup_migration(short=short)

    @db_app.command()
    def score_board() -> None:
        """Compute score board."""
        engine = build_engine()
        compute_score_board(engine)

    @db_app.command()
    def sync() -> None:
        """Synchronize official results and push them to admin with web
        scraping the world cup wikipedia page"""
        engine = build_engine()
        synchronize_official_results(engine)

    return db_app


def make_env_typer() -> typer.Typer:
    env_typer = typer.Typer()

    @env_typer.command()
    def init(  # noqa: PLR0913
        *,
        debug: bool = typer.Option(False, "--debug", "-d", help="Run in debug mode", prompt=True),  # noqa: FBT003
        host: str = typer.Option("localhost", "--host", "-H", help="Database host", prompt=True),
        user: str = typer.Option("yak", "--user", "-u", help="Database username", prompt=True),
        password: str = typer.Option(..., hide_input=True, help="Database password", prompt=True),
        port: int = typer.Option(5432, "--port", "-p", help="Database port", prompt=True),
        database: str = typer.Option(
            "yak_db", "--database", "-D", help="Database name", prompt=True
        ),
        jwt_expiration: int = typer.Option(
            3600, "--jwt-expiration", "-j", help="JWT expiration time in seconds", prompt=True
        ),
        competition: str = typer.Option(
            ..., "--competition", "-c", help="Competition name", prompt=True
        ),
    ) -> None:
        """Build the env files you need to start the server."""
        init_env(debug, host, user, password, competition, database, jwt_expiration, port)

    return env_typer


@app.command()
def openapi() -> None:
    """Print the openapi.json file."""
    app = create_app()
    typer.echo(json.dumps(app.openapi(), separators=(",", ":")))


app.add_typer(make_db_app(), name="db")
app.add_typer(make_env_typer(), name="env")


if __name__ == "__main__":  # pragma: no cover
    app()
