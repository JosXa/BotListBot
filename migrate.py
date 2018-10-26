import os
from pprint import pprint

from decouple import config
from peewee import IntegrityError, Field
from playhouse.db_url import connect
from playhouse.migrate import SqliteMigrator, PostgresqlMigrator
from playhouse.postgres_ext import PostgresqlExtDatabase
from playhouse.sqliteq import SqliteQueueDatabase

from models import *
from models import Bot, User, Suggestion
from models.keywordmodel import Keyword

_sqlite_db = SqliteQueueDatabase('C:/data/botlistbot/botlistbot.sqlite3')
_postgresql_db = connect('postgresql://postgres:ne1d8b6c@localhost:5432/botlistbot')
_postgresql_db.autorollback = True

sqlite_migrator = SqliteMigrator(_sqlite_db)
postgresql_migrator = PostgresqlMigrator(_postgresql_db)

models = [Country, User, APIAccess, Category, Revision, Bot, Channel, Favorite, Group, Keyword, Notifications,
          Statistic, Suggestion]

for m in models:
    print(m.__name__)
    m._meta.database = _sqlite_db

    fetched_all = list(m.select().dicts())

    m._meta.database = _postgresql_db

    m.drop_table(fail_silently=True, cascade=True)
    m.create_table(fail_silently=True)

    for f in fetched_all:
        # try:
        try:
            m.insert(f).execute()
        except IntegrityError as e:
            m._meta.database.rollback()
            for k, v in f.items():
                if v is not None:
                    continue
                field: Field = getattr(m, k)
                if not field.null:
                    if hasattr(field, 'default'):
                        f[k] = field.default
                    else:
                        print('has no default')
            try:
                m.insert(f).execute()
            except IntegrityError as e:

                # TODO: enable
                print(f'Skiped entry {f} because {e}.')

                m._meta.database.rollback()

            # except Exception as e:
            #     print(f'Skipped {m.__name__} because {e}')
    # m.insert_many(fetched_all).execute()
