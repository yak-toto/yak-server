import click

from yak_server import create_app

from .database import (
    backup_database,
    create_admin,
    create_database,
    delete_database,
    drop_database,
    initialize_database,
)


@click.command()
def create():
    """Create all database tables"""
    app = create_app()
    with app.app_context():
        create_database(app)


@click.command()
def init():
    """Initialize database"""
    app = create_app()
    with app.app_context():
        initialize_database(app)


@click.command()
def drop():
    """Drop all tables"""
    app = create_app()
    with app.app_context():
        drop_database(app)


@click.command()
def delete():
    """Delete all records"""
    app = create_app()
    with app.app_context():
        delete_database(app)


@click.command()
def admin():
    """Create admin account in database"""
    app = create_app()
    with app.app_context():
        create_admin(app)


@click.command()
def backup():
    """Backup database in a sql file"""
    app = create_app()
    with app.app_context():
        backup_database(app)


@click.group()
def db():
    pass


db.add_command(create)
db.add_command(init)
db.add_command(drop)
db.add_command(delete)
db.add_command(admin)
db.add_command(backup)


@click.group()
def main():
    pass


main.add_command(db)
