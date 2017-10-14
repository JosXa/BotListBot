from playhouse.migrate import SqliteMigrator, BooleanField, migrate

import appglobals
from model import Bot


migrator = SqliteMigrator(appglobals.db)

migrate(
    migrator.add_column("bot", "userbot", BooleanField(default=False))
    # migrator.rename_column("transaction", "document", "document_id"),
    # migrator.rename_column("document", "user", "user_id"),
)

print('Setting all bots to userbot=False.......')
for b in Bot.select():
    b.userbot = False
    b.save()

