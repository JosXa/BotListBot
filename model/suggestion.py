# -*- coding: utf-8 -*-
import datetime
from peewee import *

import const
import settings
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
    BOOLEAN_ACTIONS = ['inlinequeries', 'official', 'offline', 'spam']

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

        if self._value == 'None':
            return None

        if self.action in self.BOOLEAN_ACTIONS:
            return bool(self._value)
        elif self.action == 'category':
            return Category.get(id=self._value)
        elif self.action == 'country':
            if self._value is None:
                return None
            return Country.get(id=self._value)
        else:
            return str(self._value) if self._value else None

    @value.setter
    def value(self, value):
        self._value = value

    @staticmethod
    def add_or_update(user, action, subject, value):
        from model import Statistic
        # value may be None
        already_exists = Suggestion.get_pending(action, subject, user)
        if already_exists:
            # Does the new suggestion reset the value?
            if value == getattr(already_exists.subject, action):

                already_exists.delete_instance()
                return None

            already_exists.value = value
            already_exists.save()

            Statistic.of(user, 'made changes to their suggestion: ', already_exists._md_plaintext())

            return already_exists
        else:
            new_suggestion = Suggestion(user=user, action=action, date=datetime.date.today(),
                                        subject=subject, value=value)
            new_suggestion.save()
            Statistic.of(user, 'suggestion', new_suggestion._md_plaintext())
            return new_suggestion

    @staticmethod
    def select_all(exclude_user=None):
        Suggestion.delete_missing()
        if exclude_user:
            return Suggestion.select().where(Suggestion.executed == False, Suggestion.user != exclude_user)
        else:
            return Suggestion.select().where(Suggestion.executed == False)

    @staticmethod
    def select_all_of_user(user):
        Suggestion.delete_missing()
        return Suggestion.select().where(Suggestion.executed == False, Suggestion.user == user)

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
        ).count() >= settings.SUGGESTION_LIMIT

    @staticmethod
    def pending_for_bot(bot, user):
        pending = Suggestion.select().where(
            Suggestion.executed == False,
            Suggestion.user == user,
            Suggestion.subject == bot
        )
        return {s.action: s.value for s in pending}

    def apply(self):
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
            if self._value == 'None' or self._value is None:
                self.subject.country = None
            else:
                from model import Country
                try:
                    con = Country.get(id=self._value)
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

    def _md_plaintext(self):
        uname = util.escape_markdown(self.subject.username)
        value = self.value

        text = ''
        if self.action == 'category':
            from model import Category
            try:
                cat = Category.get(id=self.value)
                text += "move {} ➜ {}".format(uname, cat.name)
            except Category.DoesNotExist:
                raise AttributeError("Category to change to does not exist.")
        elif self.action == 'name':
            text += "set name {} ➜ {}".format(uname, str(value))
        elif self.action == 'username':
            text += "set username {} ➜ {}".format(uname, str(value))
        elif self.action == 'description':
            text += "change description text of {}".format(uname)
        elif self.action == 'extra':
            text += "change extra text {}".format(uname)
        elif self.action == 'country':
            text += "change country {} ➜ ".format(uname)
            if self._value == 'None' or self._value is None:
                text += "None"
            else:
                from model import Country
                try:
                    con = Country.get(id=self._value)
                    text += str(con)
                except Country.DoesNotExist:
                    raise AttributeError("Country to change to does not exist.")
        elif self.action == 'inlinequeries':
            text += "toggle inlinequeries {} ➜ {}".format(uname, str(value))
        elif self.action == 'official':
            text += "toggle official {} ➜ {}".format(uname, str(value))
        elif self.action == 'offline':
            text += "set {} {}".format('offline' if bool(value) else 'online', uname)
        elif self.action == 'spam':
            text += "mark {} as spammy".format(uname)
        return text

    def __str__(self):
        text = str(self.user) + ": " + self._md_plaintext()
        return text.encode('utf-8').decode('utf-8')
