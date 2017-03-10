# -*- coding: utf-8 -*-
import emoji
from peewee import *

from model.bot import Bot
from model.basemodel import BaseModel


class Keyword(BaseModel):
    id = PrimaryKeyField()
    name = CharField()
    entity = ForeignKeyField(Bot)

    def __str__(self):
        return '#' + self.name

