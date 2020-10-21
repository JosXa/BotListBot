# -*- coding: utf-8 -*-
import emoji
from peewee import *

from botlistbot.models.basemodel import BaseModel


class Country(BaseModel):
    id = PrimaryKeyField()
    name = CharField(unique=True)
    emoji = CharField()

    @property
    def emojized(self):
        return emoji.emojize(self.emoji, use_aliases=True)

    def __str__(self):
        return self.name + ' ' + self.emojized
