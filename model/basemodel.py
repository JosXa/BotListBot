# -*- coding: utf-8 -*-
from peewee import *
from playhouse.sqlite_ext import FTSModel

from appglobals import db


class BaseModel(Model):
    class Meta:
        database = db


class BaseFTSModel(FTSModel):
    class Meta:
        database = db
        extension_options = {'tokenize': 'porter'}
