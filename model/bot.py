# -*- coding: utf-8 -*-
import datetime
from typing import List

from peewee import *

import helpers
import util
from model.basemodel import BaseModel
from model.category import Category
from model.country import Country
from model.user import User


class Bot(BaseModel):
    id = PrimaryKeyField()
    category = ForeignKeyField(Category, null=True)
    name = CharField(null=True)
    username = CharField(unique=True)
    description = TextField(null=True)
    date_added = DateField()
    country = ForeignKeyField(Country, null=True)
    inlinequeries = BooleanField(default=False)
    official = BooleanField(default=False)
    extra = CharField(null=True)
    offline = BooleanField(default=False)
    spam = BooleanField(default=False)

    approved = BooleanField(default=True)
    submitted_by = ForeignKeyField(User, null=True)

    @property
    def serialize(self):
        return {
            'id': self.id,
            'category_id': self.category.id,
            # 'name': self.name,
            'username': self.username,
            'description': self.description,
            'date_added': self.date_added,
            'inlinequeries': self.inlinequeries,
            'official': self.official,
            'extra_text': self.extra,
            'offline': self.offline,
            'spam': self.spam,
            'botlist_url': helpers.botlist_url_for_category(self.category),
        }

    @property
    def is_new(self):
        import const
        today = datetime.date.today()
        delta = datetime.timedelta(days=const.BOT_CONSIDERED_NEW)
        result = today - self.date_added < delta
        return result

    def __str__(self):
        return util.escape_markdown(self.str_no_md).encode('utf-8').decode('utf-8')

    @property
    def detail_text(self):
        from model import Keyword
        keywords = Keyword.select().where(Keyword.entity == self)
        txt = '{}'.format(self.__str__())
        txt += '\n_{}_'.format(util.escape_markdown(self.name)) if self.name else ''
        txt += '\n\n{}'.format(self.description) if self.description else ''
        txt += util.escape_markdown(
            '\n\nKeywords: {}'.format(', '.join([str(k) for k in keywords])) if keywords else '')
        return txt

    @property
    def str_no_md(self):
        return ('💤 ' if self.offline else '') + \
               ('🚮 ' if self.spam else '') + \
               ('🆕 ' if self.is_new else '') + \
               self.username + \
               (' ' if any([self.inlinequeries, self.official, self.country]) else '') + \
               ('🔎' if self.inlinequeries else '') + \
               ('🔹' if self.official else '') + \
               (self.country.emoji if self.country else '') + \
               (' ' + self.extra if self.extra else '')

    @staticmethod
    def by_username(username: str):
        result = Bot.select().where(fn.lower(Bot.username) == username.lower())
        if len(result) > 0:
            return result[0]
        else:
            raise Bot.DoesNotExist()

    @staticmethod
    def many_by_usernames(names: List):
        results = Bot.select().where(fn.lower(Bot.username) << [n.lower() for n in names])
        if len(results) > 0:
            return results
        else:
            raise Bot.DoesNotExist()

    @staticmethod
    def of_category(category):
        return Bot.select().where(Bot.category == category, Bot.approved == True).order_by(fn.Lower(Bot.username))

    @staticmethod
    def get_new_bots():
        import const
        return Bot.select().where(
            (Bot.approved == True) & (
                Bot.date_added.between(
                    datetime.date.today() - datetime.timedelta(days=const.BOT_CONSIDERED_NEW),
                    datetime.date.today()
                )
            ))

    @staticmethod
    def get_new_bots_str():
        return '\n'.join(['     {}'.format(str(b)) for b in Bot.get_new_bots()])

    @property
    def keywords(self):
        from model.keywordmodel import Keyword
        return Keyword.select().where(Keyword.entity == self)
