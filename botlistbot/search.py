import re

from peewee import fn

from botlistbot import settings
from botlistbot.models import Bot
from botlistbot.models import Category
from botlistbot.models import Keyword
from botlistbot.models.revision import Revision


def search_bots(query):
    query = query.lower().strip()
    split = query.split(' ')

    # easter egg
    if query in ('awesome bot', 'great bot', 'superb bot', 'best bot', 'best bot ever'):
        return [Bot.by_username('@botlistbot')]

    # exact results
    where_query = (
        (fn.lower(Bot.username).contains(query) |
         fn.lower(Bot.name) << split |
         fn.lower(Bot.extra) ** query) &
        (Bot.revision <= Revision.get_instance().nr &
         Bot.approved == True & Bot.disabled == False)
    )
    results = set(Bot.select().distinct().where(where_query))

    # keyword results
    keyword_results = Bot.select(Bot).join(Keyword).where(
        (fn.lower(Keyword.name) << split) &
        (Bot.revision <= Revision.get_instance().nr) &
        (Bot.approved == True & Bot.disabled == False)
    )
    results.update(keyword_results)

    # many @usernames
    usernames = re.findall(settings.REGEX_BOT_ONLY, query)
    if usernames:
        try:
            bots = Bot.many_by_usernames(usernames)
            print([b.username for b in bots])
            results.update(bots)
        except Bot.DoesNotExist:
            pass

    return list(results)


def search_categories(query):
    query = query.lower().strip()
    categories = Category.select().where(
        (fn.lower(Category.name).contains(query)) |
        (fn.lower(Category.extra).contains(query))
    )
    return categories
