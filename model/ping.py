# -*- coding: utf-8 -*-
from typing import List

from peewee import *

import helpers
import settings
import util
from model import Bot
from model.basemodel import BaseModel
from model.category import Category
from model.country import Country
from model.revision import Revision
from model.user import User


class Ping(BaseModel):
    bot = ForeignKeyField(Bot, unique=True)
    last_ping = DateTimeField()
    last_response = DateTimeField()
