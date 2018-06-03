from playhouse.migrate import SqliteMigrator, BooleanField, migrate, IntegerField
from peewee import *

import appglobals
from model import Bot, User, Suggestion
from model.basemodel import EnumField
from model.keywordmodel import Keyword

migrator = SqliteMigrator(appglobals.db)

# migrate(
# )

to_add = ["kek", "tus"]
bot = Bot.get(username='@bold')
Keyword.insert_many([dict(name=k, entity=bot) for k in to_add]).execute()
