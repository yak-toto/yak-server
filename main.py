import asyncio
from uuid import UUID

from yak_server_db import DatabaseConnection, Group

from yak_server.database import compute_database_uri_without_client, get_postgres_settings

postgres_settings = get_postgres_settings()

database_url = compute_database_uri_without_client(
    postgres_settings.host,
    postgres_settings.user,
    postgres_settings.password,
    postgres_settings.port,
    postgres_settings.db,
)


def print_group(group: Group) -> None:
    print(
        f"Group(id={group.id}, code={group.code}, description_en={group.description_en}, description_fr={group.description_fr}, index={group.index}, phase_id={group.phase_id})"
    )


async def query_all_groups() -> None:
    db = await DatabaseConnection.connect(database_url)

    groups = await db.query_group().select_all()

    for group in groups:
        print_group(group)


async def query_one_group() -> None:
    db = await DatabaseConnection.connect(database_url)

    group = await db.query_group().select_one(UUID("4ffad91a-faa2-4b44-9887-6d05957c6882"))

    if group is not None:
        print_group(group)
    else:
        print("Group not found")

    group = await db.query_group().select_one(UUID("f90d3a51-7fbd-4a25-902a-60bbcb919d50"))

    if group is not None:
        print_group(group)
    else:
        print("Group not found")


async def count_groups() -> None:
    db = await DatabaseConnection.connect(database_url)

    count = await db.query_group().count()
    print(f"Total groups: {count}")


asyncio.run(query_all_groups())

print()

asyncio.run(query_one_group())

print()
asyncio.run(count_groups())
