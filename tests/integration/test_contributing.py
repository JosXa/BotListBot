import re

import settings
from model import Bot
from tgintegration import BotIntegrationClient


def test_new(client: BotIntegrationClient):
    uname = '@test__bot'
    try:
        try:
            b = Bot.get(username=uname)
            b.delete_instance()
        except Bot.DoesNotExist:
            pass

        res = client.send_command_await("new", [uname])
        if client.get_me().id in settings.MODERATORS:
            assert 'is currently pending' in res.full_text.lower()
            assert res.inline_keyboards[0].find_button(r'.*Accept.*')
        else:
            assert re.search('you submitted.*for approval', res.full_text, re.IGNORECASE)
    finally:
        Bot.delete().where(Bot.username == uname)
