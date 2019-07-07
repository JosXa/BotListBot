import asyncio
import os
from pathlib import Path

from decouple import config
from peewee import Proxy
from playhouse.db_url import connect

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
ACCOUNTS_DIR = Path(ROOT_DIR) / "accounts"

_db_path = config('DATABASE_URL')

_auto_typed_db = connect(_db_path)
_auto_typed_db.autorollback = True

db = Proxy()
db.initialize(_auto_typed_db)

loop = asyncio.get_event_loop()
