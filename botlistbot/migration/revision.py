import os

from decouple import config
from playhouse.migrate import SqliteMigrator, IntegerField, migrate
from playhouse.sqlite_ext import SqliteExtDatabase

from botlistbot.models.revision import Revision

db_path = config('DATABASE_URL', default=os.path.expanduser('~/botlistbot.sqlite3'))
db = SqliteExtDatabase(db_path)

migrator = SqliteMigrator(db)

revision = IntegerField(default=100)

with db.transaction():
    migrate(
        migrator.add_column('bot', 'revision', revision),
    )

Revision.create_table(fail_silently=True)
Revision.insert({'nr': 101}).execute()
