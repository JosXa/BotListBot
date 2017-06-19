# -*- coding: utf-8 -*-
import datetime
from peewee import *

import const
import util
from model import Bot
from model import User
from model.basemodel import BaseModel


class Suggestion(BaseModel):
    # class Action:
    #     OFFLINE = 'offline'
    #     SPAM = 'spam'
    #     CHANGE_CATEGORY = 'category'
    #     CHANGE_DESCRIPTION = 'description'
    #     CHANGE_NAME = 'name'
    #     CHANGE_EXTRA = 'extra'
    #     CHANGE_ = 'extra'
    #
    #     @staticmethod
    #     def textual():
    #         return [Suggestion.Action.CHANGE_DESCRIPTION]
    ACTIONS = [
        'category',
        'name',
        'username',
        'description',
        'country',
        'inlinequeries',
        'official',
        'extra',
        'offline',
        'spam'
    ]
    TEXTUAL_ACTIONS = ['description', 'extra']
    BOOLEAN_ACTIONS = ['inlinequeries', 'official', 'extra', 'offline', 'spam']

    user = ForeignKeyField(User)
    date = DateField()
    subject = ForeignKeyField(Bot)
    _value = CharField(null=True, db_column='value')
    executed = BooleanField(default=False)
    action = CharField(choices=ACTIONS)

    @property
    def value(self):
        # cast types
        from model import Category
        from model import Country

        if self.action in self.BOOLEAN_ACTIONS:
            return bool(self._value)
        elif self.action == 'category':
            return Category.get(id=self._value)
        elif self.action == 'country':
            return Country.get(id=self._value)
        else:
            return str(self._value)

    @value.setter
    def value(self, value):
        self._value = value

    @staticmethod
    def add_or_update(user, action, subject, value):
        # value may be None
        already_exists = Suggestion.get_pending(action, subject, user)
        if already_exists:
            # Does the new suggestion reset the value?
            if value == getattr(already_exists.subject, action):

                already_exists.delete_instance()
                return None

            already_exists.value = value
            already_exists.save()

            return already_exists
        else:
            new_suggestion = Suggestion(user=user, action=action, date=datetime.date.today(),
                                        subject=subject, value=value)
            new_suggestion.save()
            return new_suggestion

    @staticmethod
    def select_all(exclude_user=None):
        Suggestion.delete_missing()
        if exclude_user:
            return Suggestion.select().where(Suggestion.executed == False, Suggestion.user != exclude_user)
        else:
            return Suggestion.select().where(Suggestion.executed == False)

    @staticmethod
    def get_pending(action, bot, user):
        try:
            return Suggestion.get(action=action, subject=bot, user=user, executed=False)
        except Suggestion.DoesNotExist:
            return None

    @staticmethod
    def over_limit(user):
        return Suggestion.select().where(
            Suggestion.user == user,
            Suggestion.executed == False
        ).count() >= const.SUGGESTION_LIMIT

    @staticmethod
    def pending_for_bot(bot, user):
        pending = Suggestion.select().where(
            Suggestion.executed == False,
            Suggestion.user == user,
            Suggestion.subject == bot
        )
        return {s.action: s.value for s in pending}

    def execute(self):
        try:
            if self.subject is None:
                self.delete_instance()
                return False
        except Bot.DoesNotExist:
            self.delete_instance()
            return False

        if self.action == 'category':
            from model import Category
            try:
                cat = Category.get(Category.id == self.value)
                self.subject.category = cat
            except Category.DoesNotExist:
                raise AttributeError("Category to change to does not exist.")
        elif self.action == 'name':
            self.subject.name = self.value
        elif self.action == 'username':
            self.subject.username = self.value
        elif self.action == 'description':
            self.subject.description = self.value
        elif self.action == 'extra':
            self.subject.extra = self.value
        elif self.action == 'country':
            if self.value == 'None' or self.value is None:
                self.subject.country = None
            else:
                from model import Country
                try:
                    con = Country.get(id=self.value)
                    self.subject.country = con
                except Country.DoesNotExist:
                    raise AttributeError("Country to change to does not exist.")
        elif self.action == 'inlinequeries':
            self.subject.inlinequeries = bool(self.value)
        elif self.action == 'official':
            self.subject.official = bool(self.value)
        elif self.action == 'offline':
            self.subject.offline = bool(self.value)
        elif self.action == 'spam':
            self.subject.spam = bool(self.value)

        self.subject.save()
        self.executed = True
        self.save()
        return True

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
        value = str(self.value)

        text = str(self.user) + ": "
        if self.action == 'category':
            from model import Category
            try:
                cat = Category.get(id=self.value)
                print(str(cat))
                text += "move {} ➜ {}".format(uname, cat.name)
            except Category.DoesNotExist:
                raise AttributeError("Category to change to does not exist.")
        elif self.action == 'name':
            text += "set name {} ➜ {}".format(uname, value)
        elif self.action == 'username':
            text += "set username {} ➜ {}".format(uname, value)
        elif self.action == 'description':
            text += "change description text {}".format(uname)
        elif self.action == 'extra':
            text += "change extra text {}".format(uname)
        elif self.action == 'country':
            from model import Country
            try:
                con = Country.get(id=self.value)
                text += "change country {} ➜ {}".format(uname, str(con))
            except Country.DoesNotExist:
                raise AttributeError("Country to change to does not exist.")
        elif self.action == 'inlinequeries':
            text += "toggle inlinequeries {} ➜ {}".format(uname, value)
        elif self.action == 'official':
            text += "toggle official {} ➜ {}".format(uname, value)
        elif self.action == 'offline':
            text += "set offline {}".format(uname)
        elif self.action == 'spam':
            text += "mark {} as spammy".format(uname)
        return text.encode('utf-8').decode('utf-8')
