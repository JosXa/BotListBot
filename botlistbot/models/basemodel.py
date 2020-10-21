# -*- coding: utf-8 -*-
from enum import Enum

from peewee import *
from playhouse.sqlite_ext import FTSModel

from botlistbot.appglobals import db


class BaseModel(Model):
    class Meta:
        database = db


class BaseFTSModel(FTSModel):
    class Meta:
        database = db
        extension_options = {'tokenize': 'porter'}


class EnumField(SmallIntegerField):
    def __init__(self, enum_type, *args, **kwargs):
        self.enum_type = enum_type
        super(SmallIntegerField, self).__init__(*args, **kwargs)

    def db_value(self, value):
        if isinstance(value, Enum):
            return value.value
        if value is None:
            return None
        return value.value

    def python_value(self, value: int):
        result = self.enum_type(value) if value else None
        return result

