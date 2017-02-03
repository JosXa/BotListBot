from peewee import *

import util
from model import Bot
from model import User
from model.basemodel import BaseModel


class Suggestion(BaseModel):
    user = ForeignKeyField(User)
    action = CharField(choices=["offline"])
    date = DateField()
    subject = ForeignKeyField(Bot)

    def __str__(self):
        text = str(self.user) + ": "
        if self.action == "offline":
            text += "Set offline"
        text += " {}.".format(self.subject.username)
        return util.escape_markdown(text)
