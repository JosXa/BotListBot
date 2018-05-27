# -*- coding: utf-8 -*-
import os
from datetime import timedelta
from enum import IntEnum
from typing import List

from peewee import *
from playhouse.hybrid import hybrid_property

import helpers
import settings
import util
from model.basemodel import BaseModel, EnumField
from model.category import Category
from model.country import Country
from model.revision import Revision
from model.user import User


class Bot(BaseModel):
    class DisabledReason(IntEnum):
        # In prioritized order, cannot go from banned to offline
        banned = 10
        offline = 20

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
    spam = BooleanField(default=False)
    bot_info_version = CharField(null=True)
    restriction_reason = CharField(null=True)

    last_ping = DateTimeField(null=True)
    last_response = DateTimeField(null=True)
    disabled = BooleanField(default=False)
    disabled_reason = EnumField(DisabledReason, null=True)

    userbot = BooleanField(default=False)
    botbuilder = BooleanField(default=False)
    chat_id = IntegerField(null=True)

    approved = BooleanField(default=True)
    submitted_by = ForeignKeyField(User, null=True, related_name='submitted_by')
    approved_by = ForeignKeyField(User, null=True, related_name='approved_by')

    @hybrid_property
    def offline(self) -> bool:
        if not self.last_ping:
            return False
        return self.last_response != self.last_ping

    @hybrid_property
    def online(self) -> bool:
        return not self.offline

    @property
    def offline_for(self) -> timedelta:
        if not self.last_response:
            return timedelta(days=365 * 2)
        return self.last_ping - self.last_response if self.offline else None

    @staticmethod
    def select_approved():
        return Bot.select().where(
            Bot.approved == True,
            Bot.revision <= Revision.get_instance().nr,
            Bot.disabled == False
        )

    @staticmethod
    def select_unapproved():
        return Bot.select().where(Bot.approved == False, Bot.disabled == False)

    @staticmethod
    def select_pending_update():
        return Bot.select().where(
            Bot.approved == True,
            Bot.revision == Revision.get_instance().next,
            Bot.disabled == False
        )

    @property
    def serialize(self):
        return {
            'id'           : self.id,
            'category_id'  : self.category.id,
            # 'name': self.name,
            'username'     : self.username,
            'description'  : self.description,
            'date_added'   : self.date_added,
            'inlinequeries': self.inlinequeries,
            'official'     : self.official,
            'extra_text'   : self.extra,
            'offline'      : self.offline,
            'spam'         : self.spam,
            'botlist_url'  : helpers.botlist_url_for_category(self.category),
        }

    def disable(self, reason: DisabledReason):
        if self.disabled:
            if self.disabled_reason == reason:
                return False  # if value unchanged
            if reason.value > self.disabled_reason:
                raise ValueError("Invalid reason, cannot go from {} to {}.".format(
                    self.disabled_reason.name,
                    reason.name
                ))

        self.disabled = True
        self.disabled_reason = reason
        return True  # if value changed

    def enable(self):
        if not self.disabled:
            return False  # if value unchanged
        self.disabled = False
        self.disabled_reason = None
        return True  # if value changed

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
        result = Bot.select().where(
            fn.lower(Bot.username) == username.lower(),
            Bot.disabled == False
        )
        if len(result) > 0:
            return result[0]
        else:
            raise Bot.DoesNotExist()

    @staticmethod
    def explorable_bots():
        results = Bot.select().where(
            ~(Bot.description.is_null()),
            (Bot.approved == True),
            (Bot.revision <= Revision.get_instance().nr),
            (Bot.offline == False),
            (Bot.disabled == False)
        )
        return list(results)

    @staticmethod
    def many_by_usernames(names: List):
        results = Bot.select().where(
            (fn.lower(Bot.username) << [n.lower() for n in names]) &
            (Bot.revision <= Revision.get_instance().nr) &
            (Bot.approved == True) &
            (Bot.disabled == False)
        )
        if results:
            return results
        raise Bot.DoesNotExist

    @staticmethod
    def of_category_without_new(category):
        return Bot.select().where(
            (Bot.category == category),
            (Bot.approved == True),
            (Bot.revision <= Revision.get_instance().nr),
            (Bot.disabled == False)
        ).order_by(fn.Lower(Bot.username))

    @staticmethod
    def select_official_bots():
        return Bot.select().where(Bot.approved == True, Bot.official == True,
                                  Bot.disabled == False)

    @staticmethod
    def select_new_bots():
        return Bot.select().where(
            (Bot.revision >= Revision.get_instance().nr - settings.BOT_CONSIDERED_NEW + 1) &
            (Bot.revision < Revision.get_instance().next) &
            Bot.approved == True & Bot.disabled == False
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
