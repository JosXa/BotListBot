from pprint import pprint

from peewee import fn, Expression

from model import Bot
from model import Category
from model import Keyword


def search_bots(query):
    query = query.lower().strip()
    split = query.split(' ')

    # exact results
    where_query = (
        (fn.lower(Bot.username).contains(query)) |
        (fn.lower(Bot.name) << split) |
        (fn.lower(Bot.extra) ** query)
    )
    results = set(Bot.select().distinct().where(where_query))
    keyword_results = Bot.select(Bot).join(Keyword).where(fn.lower(Keyword.name) << split)
    results.update(keyword_results)
    return results


def search_categories(query):
    query = query.lower().strip()
    categories = Category.select().where(
        (fn.lower(Category.name).contains(query)) |
        (fn.lower(Category.extra).contains(query))
    )
    return categories

