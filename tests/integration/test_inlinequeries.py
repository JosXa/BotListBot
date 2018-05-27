import re
import time

import pytest

from model import Bot
from tgintegration import BotIntegrationClient


@pytest.fixture
def bots():
    return Bot.many_by_usernames(['@stickers', '@botlistbot', '@bold'])


def test_search(client: BotIntegrationClient, bots):
    for bot in bots:
        res = client.get_inline_bot_results(
            client.peer_id,
            bot.username
        )
        results = res.find_results(
            title_pattern=re.compile(r'{}\b.*'.format(bot.username), re.IGNORECASE)
        )
        try:
            results.pop()  # pop first, make sure now it's empty
        except KeyError:
            print(results)
            raise KeyError("No result found for {}".format(bot.username))
        assert len(results) == 0, "More than one article in inline query results for {}".format(
            bot.username)


def test_other(client: BotIntegrationClient):
    test = ["contributing", "rules", "examples"]

    for t in test:
        res = client.get_inline_bot_results(client.peer_id, t)
        assert res.find_results(
            title_pattern=re.compile(r'.*{}.*'.format(t), re.IGNORECASE)
        ), "{} did not work".format(t)
        time.sleep(1)
