# -*- coding: utf-8 -*-
import emoji
from peewee import *

from model.basemodel import BaseModel


class Category(BaseModel):
    id = PrimaryKeyField()
    emojis = CharField()
    name = CharField(unique=True)
    extra = CharField(null=True)
    current_message_id = IntegerField(null=True)

    def __str__(self):
        return '•' + emoji.emojize(self.emojis, use_aliases=True) + self.name + \
               (' - ' + self.extra if self.extra else '')
