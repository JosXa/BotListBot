# -*- coding: utf-8 -*-
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

    @staticmethod
    def delete_missing():
        # TODO: test
        for suggestion in Suggestion.select():
            if suggestion.subject is None:
                suggestion.delete_instance()


    def __str__(self):
        text = str(self.user) + ": "
        if self.action == "offline":
            text += "Set offline"
        text += " {}.".format(util.escape_markdown(self.subject.username))
        return text.encode('utf-8').decode('utf-8')

