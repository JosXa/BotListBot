import os

from decouple import config
from playhouse.sqlite_ext import SqliteExtDatabase

_db = None
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))


def db():
    global _db
    if not _db:
        db_path = config('DATABASE_URI', default=os.path.expanduser('~/botlistbot.sqlite3'))
        _db = SqliteExtDatabase(db_path)
    return _db


def disconnect():
    _db.close()


# globals
db = db()

