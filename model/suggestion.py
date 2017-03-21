# -*- coding: utf-8 -*-
from peewee import *

import util
from model import Bot
from model import User
from model.basemodel import BaseModel


class Suggestion(BaseModel):
    user = ForeignKeyField(User)
    action = CharField(choices=['offline', 'spam', 'change_category'])
    date = DateField()
    subject = ForeignKeyField(Bot)
    value = IntegerField(null=True)
    executed = BooleanField(default=False)

    @staticmethod
    def select_all():
        Suggestion.delete_missing()
        return Suggestion.select().where(Suggestion.executed == False)

    def execute(self):
        if self.action == 'offline':
            self.subject.offline = True
            self.subject.save()
            self.delete_instance()
        if self.action == 'spam':
            self.subject.spam = True
            self.subject.save()
            self.delete_instance()
        if self.action == 'change_category':
            from model import Category
            try:
                cat = Category.get(Category.id == self.value)
            except Category.DoesNotExist:
                raise AttributeError("Category to change to does not exist.")
            self.subject.category = cat
            self.subject.save()
            self.delete_instance()
        self.executed = True
        self.save()

    @staticmethod
    def delete_missing():
        for suggestion in Suggestion.select():
            try:
                if suggestion.subject is None:
                    suggestion.delete_instance()
            except Bot.DoesNotExist:
                suggestion.delete_instance()

    def __str__(self):
        uname = util.escape_markdown(self.subject.username)
        text = str(self.user) + ": "
        if self.action == "offline":
            text += "Set offline {}".format(uname)
        if self.action == "spam":
            text += "mark {} as spammy".format(uname)
        if self.action == "change_category":
            from model import Category
            try:
                cat = Category.get(Category.id == self.value)
                text += "move {} to {}".format(uname, cat.name)
            except Category.DoesNotExist:
                raise AttributeError("Category to change to does not exist.")
        text += "."
        return text.encode('utf-8').decode('utf-8')
