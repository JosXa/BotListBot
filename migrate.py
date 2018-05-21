from playhouse.migrate import SqliteMigrator, BooleanField, migrate, IntegerField
from peewee import *

import appglobals
from model import Bot, User, Suggestion
from model.basemodel import EnumField
from model.keywordmodel import KeywordSuggestion

migrator = SqliteMigrator(appglobals.db)

# TODO: manually delete Ping table
KeywordSuggestion.create_table()
#
migrate(
    migrator.add_column("bot", "bot_info_version", CharField(null=True)),
    migrator.add_column("bot", "restriction_reason", CharField(null=True)),
    migrator.add_column("bot", "disabled", BooleanField(default=False)),
    migrator.add_column("bot", "disabled_reason", EnumField(Bot.DisabledReason, null=True)),

    migrator.drop_column("bot", "offline"),
    migrator.add_column("bot", "last_ping", DateTimeField(null=True)),
    migrator.add_column("bot", "last_response", DateTimeField(null=True)),
)
