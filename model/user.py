# -*- coding: utf-8 -*-
import inflect
from peewee import *
from telegram import User as TelegramUser

from layouts import Layouts
from model.basemodel import BaseModel


class User(BaseModel):
    id = PrimaryKeyField()
    chat_id = IntegerField()
    username = CharField(null=True)
    first_name = CharField(null=True)
    last_name = CharField(null=True)
    photo = CharField(null=True)
    banned = BooleanField(default=False)
    favorites_layout = CharField(choices=Layouts.choices(), default=Layouts.default())


    @staticmethod
    def from_telegram_object(user: TelegramUser):
        try:
            u = User.get(User.chat_id == user.id)
            u.first_name = user.first_name
            u.last_name = user.last_name
            u.username = user.username
        except User.DoesNotExist:
            u = User(chat_id=user.id, username=user.username, first_name=user.first_name, last_name=user.last_name)

        u.save()
        return u

    @staticmethod
    def from_update(update):
        user = update.effective_user
        try:
            u = User.get(User.chat_id == user.id)
        except User.DoesNotExist:
            u = User(chat_id=user.id, username=user.username, first_name=user.first_name, last_name=user.last_name)
            u.save()
        return u

    @property
    def has_favorites(self):
        from model import Favorite
        return Favorite.select().where(Favorite.user == self).count() > 0

    @property
    def num_contributions(self):
        from model import Bot
        return Bot.select().where(Bot.submitted_by == self).count()

    @property
    def contributions_ordinal(self):
        p = inflect.engine()
        return p.ordinal(self.num_contributions)

    def __str__(self):
        text = '👤 '  # emoji
        full_name = ' '.join([
            self.first_name if self.first_name else '',
            self.last_name if self.last_name else ''
        ])
        if self.username:
            text += '[{}](https://t.me/{})'.format(full_name, self.username)
        else:
            text += full_name
        return text.encode('utf-8').decode('utf-8')

    @property
    def markdown_short(self):
        text = '👤 '  # emoji
        full_name = ''
        if self.first_name:
            full_name = self.first_name
        if self.username:
            text += '[{}](https://t.me/{})'.format(full_name, self.username)
        else:
            text += full_name
        return text.encode('utf-8').decode('utf-8')

    @property
    def plaintext(self):
        text = '👤 '  # emoji
        text += ' '.join([
            self.first_name if self.first_name else '',
            self.last_name if self.last_name else ''
        ])
        return text.encode('utf-8').decode('utf-8')


    @staticmethod
    def by_username(username: str):
        if username[0] == '@':
            username = username[1:]
        result = User.select().where(
            (fn.lower(User.username) == username.lower())
        )
        if len(result) > 0:
            return result[0]
        else:
            raise User.DoesNotExist()
