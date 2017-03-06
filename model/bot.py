# -*- coding: utf-8 -*-
import datetime

from peewee import *

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

    approved = BooleanField(default=True)
    submitted_by = ForeignKeyField(User, null=True)

    @property
    def is_new(self):
        import const
        today = datetime.date.today()
        delta = datetime.timedelta(days=const.BOT_CONSIDERED_NEW)
        result = today - self.date_added < delta
        return result

    def __str__(self):
        text = ('💤 ' if self.offline else '') + \
               ('🆕 ' if self.is_new else '') + \
               self.username + \
               (' ' if any([self.inlinequeries, self.official, self.country]) else '') + \
               ('🔎' if self.inlinequeries else '') + \
               ('🔹' if self.official else '') + \
               (self.country.emoji if self.country else '') + \
               (' ' + self.extra if self.extra else '')
        return util.escape_markdown(text).encode('utf-8').decode('utf-8')

    @staticmethod
    def by_username(username: str):
        result = Bot.select().where(fn.lower(Bot.username) == username.lower())
        if len(result) > 0:
            return result[0]
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
