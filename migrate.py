from playhouse.migrate import SqliteMigrator, BooleanField, migrate, IntegerField
from peewee import *

import appglobals
from models import Bot, User, Suggestion
from models.basemodel import EnumField
from models.keywordmodel import Keyword

migrator = SqliteMigrator(appglobals.db)

# migrate(
# )

to_add = ["kek", "tus"]
bot = Bot.get(username='@bold')
Keyword.insert_many([dict(name=k, entity=bot) for k in to_add]).execute()
