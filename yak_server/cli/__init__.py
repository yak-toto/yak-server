import json

import click

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
from .env import init_env, write_app_env_file, write_db_env_file


@click.group()
def app() -> None:
    """CLI for yak application"""


def make_db_app() -> click.Group:
    @click.group()
    def db_app() -> None:
        """Database related commands"""

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
    @click.option(
        "--password",
        prompt=True,
        hide_input=True,
        confirmation_prompt=True,
        required=True,
    )
    def admin(password: str) -> None:
        """Create admin account in database."""
        engine = build_engine()
        create_admin(password, engine)

    @db_app.command()
    @click.option(
        "-s",
        "--short",
        is_flag=True,
        default=False,
    )
    def migration(*, short: bool) -> None:
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


def make_env_typer() -> click.Group:
    @click.group()
    def env_app() -> None:
        """Environment related commands"""

    @env_app.command()
    @click.option("--debug/--no-debug", prompt=True, is_flag=True, default=False, show_default=True)
    @click.option(
        "-h", "--host", prompt=True, default="localhost", show_default=True, help="Database host"
    )
    @click.option("-u", "--user", prompt=True, help="Database username", required=True)
    @click.option("--password", prompt=True, hide_input=True, required=True)
    @click.option(
        "-p",
        "--port",
        prompt=True,
        default=5432,
        show_default=1,
        help="Database port",
        required=True,
    )
    @click.option(
        "--database",
        "-D",
        prompt=True,
        default="yak_db",
        help="Database name",
        show_default=True,
    )
    @click.option(
        "--jwt-expiration",
        "-j",
        prompt=True,
        default=3600,
        show_default=True,
        help="JWT expiration time in seconds",
    )
    @click.option(
        "--jwt-refresh-expiration",
        "-jrf",
        prompt=True,
        default=3600,
        show_default=True,
        help="JWT refresh expiration time in seconds",
    )
    @click.option("--competition", "-c", prompt=True, help="Competition name", required=True)
    def all(  # noqa: A001, PLR0913
        *,
        debug: bool,
        host: str,
        user: str,
        password: str,
        port: int,
        database: str,
        jwt_expiration: int,
        jwt_refresh_expiration: int,
        competition: str,
    ) -> None:
        """Build the env files you need to start the server."""
        init_env(
            debug,
            host,
            user,
            password,
            competition,
            database,
            jwt_expiration,
            jwt_refresh_expiration,
            port,
        )

    @env_app.command()
    @click.option(
        "-h", "--host", prompt=True, default="localhost", show_default=True, help="Database host"
    )
    @click.option("-u", "--user", prompt=True, help="Database username", required=True)
    @click.option("--password", prompt=True, hide_input=True, required=True)
    @click.option(
        "-p",
        "--port",
        prompt=True,
        default=5432,
        show_default=1,
        help="Database port",
        required=True,
    )
    @click.option(
        "--database",
        "-D",
        prompt=True,
        default="yak_db",
        help="Database name",
        show_default=True,
    )
    def db(*, host: str, user: str, password: str, port: int, database: str) -> None:
        """Build the env files you need to setup database."""
        write_db_env_file(host, user, password, port, database)

    @env_app.command()
    @click.option("--debug/--no-debug", prompt=True, is_flag=True, default=False, show_default=True)
    @click.option(
        "--jwt-expiration",
        "-j",
        prompt=True,
        default=3600,
        show_default=True,
        help="JWT expiration time in seconds",
    )
    @click.option(
        "--jwt-refresh-expiration",
        "-jrf",
        prompt=True,
        default=3600,
        show_default=True,
        help="JWT refresh expiration time in seconds",
    )
    @click.option("--competition", "-c", prompt=True, help="Competition name", required=True)
    def app(
        *, debug: bool, jwt_expiration: int, jwt_refresh_expiration: int, competition: str
    ) -> None:
        """Build the env files you need to setup application."""
        write_app_env_file(debug, jwt_expiration, jwt_refresh_expiration, competition)

    return env_app


@app.command()
def openapi() -> None:
    """Print the openapi.json file."""
    app = create_app()
    click.echo(json.dumps(app.openapi(), separators=(",", ":")))


app.add_command(make_db_app(), name="db")
app.add_command(make_env_typer(), name="env")


if __name__ == "__main__":  # pragma: no cover
    app()
