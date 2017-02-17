# -*- coding: utf-8 -*-
from peewee import *

from appglobals import db


class BaseModel(Model):
    class Meta:
        database = db
