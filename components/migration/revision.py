import os

from playhouse.migrate import SqliteMigrator, IntegerField, migrate
from playhouse.sqlite_ext import SqliteExtDatabase

from model.revision import Revision

DB_NAME = os.path.expanduser("~/database-botlist.db")
db = SqliteExtDatabase(DB_NAME)

migrator = SqliteMigrator(db)

revision = IntegerField(default=100)

with db.transaction():
    migrate(
        migrator.add_column('bot', 'revision', revision),
    )

Revision.create_table(fail_silently=True)
Revision.insert({'nr': 100}).execute()