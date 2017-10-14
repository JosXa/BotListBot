# -*- coding: utf-8 -*-
import os
from typing import List

from peewee import *

import helpers
import settings
import util
from model.basemodel import BaseModel
from model.category import Category
from model.country import Country
from model.revision import Revision
from model.user import User


class Bot(BaseModel):
    id = PrimaryKeyField()
    revision = IntegerField()
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
    userbot = BooleanField(default=False)

    approved = BooleanField(default=True)
    submitted_by = ForeignKeyField(User, null=True, related_name='submitted_by')
    approved_by = ForeignKeyField(User, null=True, related_name='approved_by')

    @staticmethod
    def select_approved():
        return Bot.select().where(Bot.approved == True, Bot.revision <= Revision.get_instance().nr)

    @staticmethod
    def select_unapproved():
        return Bot.select().where(Bot.approved == False)

    @staticmethod
    def select_pending_update():
        return Bot.select().where(Bot.approved == True,
                                  Bot.revision == Revision.get_instance().next)

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
        # today = datetime.date.today()
        # delta = datetime.timedelta(days=settings.BOT_CONSIDERED_NEW)
        # result = today - self.date_added <= delta
        # return result
        return self.revision >= Revision.get_instance().nr - settings.BOT_CONSIDERED_NEW + 1

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
            '\n\nKeywords: {}'.format(
                ', '.join([str(k) for k in keywords])
            ) if keywords else ''
        )
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
    def explorable_bots():
        results = Bot.select().where(
            ~(Bot.description.is_null()),
            Bot.approved == True,
            Bot.revision <= Revision.get_instance().nr
        )
        return list(results)

    @staticmethod
    def many_by_usernames(names: List):
        results = Bot.select().where(
            (fn.lower(Bot.username) << [n.lower() for n in names]) &
            (Bot.revision <= Revision.get_instance().nr &
             Bot.approved == True)
        )
        if len(results) > 0:
            return results
        else:
            raise Bot.DoesNotExist()

    @staticmethod
    def of_category_without_new(category):
        return Bot.select().where(
            Bot.category == category, Bot.approved == True,
            Bot.revision <= Revision.get_instance().nr
        ).order_by(fn.Lower(Bot.username))

    @staticmethod
    def select_official_bots():
        return Bot.select().where(Bot.approved == True, Bot.official == True)

    @staticmethod
    def select_new_bots():
        return Bot.select().where(
            (Bot.revision >= Revision.get_instance().nr - settings.BOT_CONSIDERED_NEW + 1) &
            (Bot.revision < Revision.get_instance().next) &
            Bot.approved == True
        )

    @staticmethod
    def get_official_bots_markdown():
        return '\n'.join(['     {}'.format(str(b)) for b in Bot.select_official_bots()])

    @staticmethod
    def get_new_bots_markdown():
        return '\n'.join(['     {}'.format(str(b)) for b in Bot.select_new_bots()])

    @staticmethod
    def get_pending_update_bots_markdown():
        return '\n'.join(['     {}'.format(str(b)) for b in Bot.select_pending_update()])

    @property
    def keywords(self):
        from model.keywordmodel import Keyword
        return Keyword.select().where(Keyword.entity == self)

    @property
    def thumbnail_file(self):
        path = os.path.join(settings.BOT_THUMBNAIL_DIR, self.username[1:].lower() + '.jpg')
        return path
