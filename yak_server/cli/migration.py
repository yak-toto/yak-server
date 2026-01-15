from pathlib import Path

import click

try:
    import alembic
except ImportError:  # pragma: no cover
    # Very common pattern for optional dependency imports
    alembic = None  # type: ignore[assignment]


def print_export_command(alembic_ini_path: Path) -> None:
    click.echo(f"export ALEMBIC_CONFIG={alembic_ini_path}")


def setup_migration(*, short: bool = False) -> None:
    alembic_ini_path = (Path(__file__).parents[1] / "alembic.ini").resolve()

    if not alembic_ini_path.exists():
        alembic_ini_path = (Path(__file__).parents[2] / "alembic.ini").resolve()

    if short is True:
        print_export_command(alembic_ini_path)
    else:
        click.echo(
            "To be able to run the database migration scripts, "
            "you need to run the following command:",
        )
        print_export_command(alembic_ini_path)
        click.echo()
        click.echo(
            "Follow this link for more information: "
            "https://alembic.sqlalchemy.org/en/latest/tutorial.html#editing-the-ini-file",
        )

        if alembic is None:
            click.echo()
            click.echo(
                "To enable migration using alembic, please run: "
                "uv pip install yak-server[db_migration]",
            )
