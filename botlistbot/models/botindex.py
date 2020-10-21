from playhouse.sqlite_ext import *

from botlistbot.models.basemodel import BaseFTSModel


class BotIndex(BaseFTSModel):
    name = SearchField()
    description = SearchField()
    extra = SearchField()

    # http://docs.peewee-orm.com/en/latest/peewee/playhouse.html

    @staticmethod
    def save_bot(bot):
        pass
        # bot_index = BotIndex.get()
        #     # TODO
        # BotIndex.insert({
        #     BotIndex.name: bot.name,
        #     BotIndex.description: bot.description,
        #     BotIndex.extra: bot.extra}).execute()
        # })
