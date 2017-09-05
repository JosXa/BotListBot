import os

from playhouse.sqlite_ext import SqliteExtDatabase

_db = None
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_NAME = os.path.expanduser("~/database-botlist.db")


def db():
    global _db
    if not _db:
        db_path = os.path.join(ROOT_DIR, DB_NAME)
        _db = SqliteExtDatabase(db_path)
    return _db


def disconnect():
    pass
    # _db.close()


# globals
db = db()

