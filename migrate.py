from playhouse.migrate import SqliteMigrator, BooleanField, migrate, IntegerField

import appglobals
from model import Bot, User

migrator = SqliteMigrator(appglobals.db)

# migrate(
#     migrator.add_column("bot", "userbot", BooleanField(default=False))
#     # migrator.rename_column("transaction", "document", "document_id"),
#     # migrator.rename_column("document", "user", "user_id"),
# )
#
# print('Setting all bots to userbot=False.......')
# for b in Bot.select():
#     b.userbot = False
#     b.save()

# try:
#     User.botlist_user_instance().delete_instance()
# except:
#     pass


migrate(
    # migrator.rename_column("bot", "manybot", "botbuilder"),
    # migrator.add_column("bot", "botbuilder", BooleanField(default=False))
    migrator.add_column("bot", "chat_id", IntegerField(null=True))
    # migrator.rename_column("document", "user", "user_id"),
)

# print('Setting all bots to botbuilder=False.......')
# for b in Bot.select():
#     b.botbuilder = False
#     b.save()
