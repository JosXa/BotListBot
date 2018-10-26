import asyncio
import os

from decouple import config
from playhouse.sqliteq import SqliteQueueDatabase
from redis import StrictRedis

_db = None
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))


def db():
    global _db
    if not _db:
        db_path = config('DATABASE_URL', default=os.path.expanduser('~/data/botlistbot.sqlite3'))
        _db = SqliteQueueDatabase(db_path)
    return _db


def disconnect():
    # global _db
    # _db.close()
    pass  # I assume this is done by peewee automatically upon receiving a signal


redis = StrictRedis(config("REDIS_URL", default=None))

# globals
db = db()

loop = asyncio.get_event_loop()

# redis = StrictRedis(host='localhost', port=6379, db=0)
