# -*- coding: utf-8 -*-
import emoji
from peewee import *

from botlistbot import const
from botlistbot import helpers
from botlistbot.models.basemodel import BaseModel


class Category(BaseModel):
    id = PrimaryKeyField()
    order = IntegerField(unique=True)
    emojis = CharField()
    name = CharField(unique=True)
    extra = CharField(null=True)
    current_message_id = IntegerField(null=True)

    @staticmethod
    def select_all():
        return Category.select().order_by(Category.order)

    @property
    def serialize(self):
        return {
            'id': self.id,
            'name': self.name,
            'emojis': self.emojis,
            'extra_text': self.extra,
            'botlist_url': helpers.botlist_url_for_category(self)
        }

    def __str__(self):
        return '•' + emoji.emojize(self.emojis, use_aliases=True) + self.name + \
               (' - ' + self.extra if self.extra else '')
