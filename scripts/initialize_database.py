import sys

from pathlib import Path

botlistbot_path = str((Path(__file__).parent.parent / "botlistbot").absolute())
sys.path.append(botlistbot_path)

from pprint import pprint

from peewee import Proxy
from playhouse.db_url import connect
from playhouse.migrate import PostgresqlMigrator

from botlistbot import appglobals
from botlistbot.models import *
from botlistbot.models import Bot, User, Suggestion
from botlistbot.models.keywordmodel import Keyword

connection = connect(appglobals.DATABASE_PATH)
# connection = connect("sqlite:///:memory:")

connection.autorollback = True
database = Proxy()
database.initialize(connection)

postgresql_migrator = PostgresqlMigrator(database)

create_order = [
    Country,
    User,
    APIAccess,
    Category,
    Revision,
    Bot,
    Channel,
    Favorite,
    Group,
    Keyword,
    Notifications,
    Statistic,
    Suggestion,
]

delete_order = [
    APIAccess,
    Revision,
    Channel,
    Favorite,
    Group,
    Keyword,
    Notifications,
    Statistic,
    Suggestion,
    Bot,
    Country,
    Category,
    User,
]

for model in create_order:
    # noinspection PyProtectedMember
    model._meta.database = database


def delete_models():
    sure = input("Deleting all existing models... Are you sure? (y/n) ")
    if sure == "y":
        for m in delete_order:
            m.drop_table(safe=True)
        print("All models drop.")
    else:
        print("Nothing deleted.")


def try_create_models():
    for m in create_order:
        m.create_table(safe=True)
    print("Created models if they did not exist yet.")


def seed_database():
    print("Seeding database...")
    categories = [
        {**c, **{"order": n + 1, "current_message_id": None}}
        for n, c in enumerate(
            [
                {"name": "Miscellaneous", "emojis": "🌀", "extra": "Miscelaneo"},
                {"name": "Social", "emojis": "👥📢", "extra": None},
                {"name": "Promoting", "emojis": "🙋👋🏼", "extra": "Divulgación"},
            ]
        )
    ]
    with database.atomic():
        Category.insert_many(categories).execute()
    print("Inserted categories:")
    pprint(categories)
    print()

    REVISION_NR = 100
    Revision.insert({"nr": REVISION_NR}).execute()
    print(f"Singleton revision {REVISION_NR} entry created.")


if __name__ == "__main__":
    if "recreate" in sys.argv:
        delete_models()
    try_create_models()
    if "seed" in sys.argv:
        seed_database()
