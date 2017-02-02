import datetime

from playhouse.sqlite_ext import JSONField

import const
import util
from model import Bot
from model import User
from model.category import Category
from model.basemodel import BaseModel
from peewee import *

from model.country import Country


class Suggestion(BaseModel):
    user = ForeignKeyField(User)
    action = CharField(choices=["offline"])
    date = DateField()
    subject = ForeignKeyField(Bot)

    def __str__(self):
        text = str(self.user) + " suggests to "
        if self.action == "offline":
            text += "set offline"
        text += " {}.".format(self.subject.username)
        return text
