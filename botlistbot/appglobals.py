import asyncio
import os
from pathlib import Path

from decouple import config
from peewee import Proxy
from playhouse.db_url import connect
from telegram.ext import JobQueue

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
ACCOUNTS_DIR = Path(ROOT_DIR) / "accounts"

DATABASE_PATH = config('DATABASE_URL')

_auto_typed_db = connect(DATABASE_PATH)
_auto_typed_db.autorollback = True

db = Proxy()
db.initialize(_auto_typed_db)

loop = asyncio.get_event_loop()

""" Global singleton ptb job_queue as I'm too lazy to rewrite everything to say `use_context=True` and propagating
the `pass_job_queue` flag across all handlers would be an even bigger nightmare. 
At some point this is going to be replaced with `CallbackContext`, but for now we're gonna live with a global. """
job_queue: JobQueue = None
