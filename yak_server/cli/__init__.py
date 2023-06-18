import click

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


@click.command()
def create() -> None:
    """Create all database tables."""
    create_database()


@click.command()
def init() -> None:
    """Initialize database."""
    app = create_app()
    initialize_database(app)


@click.command()
def drop() -> None:
    """Drop all tables."""
    app = create_app()
    drop_database(app)


@click.command()
def delete() -> None:
    """Delete all records."""
    app = create_app()
    delete_database(app)


@click.command()
def admin() -> None:
    """Create admin account in database."""
    app = create_app()
    create_admin(app)


@click.command()
def backup() -> None:
    """Backup database in a sql file."""
    backup_database()


@click.command()
def migration() -> None:
    """Help to run database migration scripts"""
    setup_migration()


@click.group()
def db() -> None:
    pass


db.add_command(create)
db.add_command(init)
db.add_command(drop)
db.add_command(delete)
db.add_command(admin)
db.add_command(backup)
db.add_command(migration)


@click.command()
def init() -> None:
    """Build the env files you need to start the server"""
    init_env()


@click.group()
def env() -> None:
    pass


env.add_command(init)


@click.group()
def main() -> None:
    pass


main.add_command(db)
main.add_command(env)
