import datetime

import const
import util
from model.category import Category
from model.basemodel import BaseModel
from peewee import *

from model.country import Country


class Bot(BaseModel):
    id = PrimaryKeyField()
    category = ForeignKeyField(Category)
    name = CharField(null=True)
    username = CharField(unique=True)
    description = TextField(null=True)
    date_added = DateField()
    country = ForeignKeyField(Country, null=True)
    inlinequeries = BooleanField(default=False)
    official = BooleanField(default=False)
    extra = CharField(null=True)

    @property
    def is_new(self):
        today = datetime.date.today()
        delta = datetime.timedelta(days=const.BOT_CONSIDERED_NEW)
        result = today - self.date_added < delta
        return result

    def __str__(self):
        text = ('🆕 ' if self.is_new else '') + \
               self.username + ' ' + \
               ('🔎' if self.inlinequeries else '') + \
               ('🔹' if self.official else '') + \
               (self.country.emoji if self.country else '')
        return util.escape_markdown(text)
