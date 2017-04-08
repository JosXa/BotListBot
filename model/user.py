# -*- coding: utf-8 -*-
from peewee import *
from telegram import User as TelegramUser
import util
from model.basemodel import BaseModel


class User(BaseModel):
    id = PrimaryKeyField()
    chat_id = IntegerField()
    username = CharField(null=True)
    first_name = CharField(null=True)
    last_name = CharField(null=True)
    photo = CharField(null=True)
    banned = BooleanField(default=False)

    @staticmethod
    def from_telegram_object(user: TelegramUser):
        try:
            u = User.get(User.chat_id == user.id)
        except User.DoesNotExist:
            u = User(chat_id=user.id, username=user.username, first_name=user.first_name, last_name=user.last_name)
            u.save()
        return u

    @staticmethod
    def from_update(update):
        try:
            user = update.message.from_user
        except (NameError, AttributeError):
            try:
                user = update.inline_query.from_user
            except (NameError, AttributeError):
                try:
                    user = update.chosen_inline_result.from_user
                except (NameError, AttributeError):
                    try:
                        user = update.callback_query.from_user
                    except (NameError, AttributeError):
                        raise ValueError("No user in update")
        try:
            u = User.get(User.chat_id == user.id)
        except User.DoesNotExist:
            u = User(chat_id=user.id, username=user.username, first_name=user.first_name, last_name=user.last_name)
            u.save()
        return u

    def __str__(self):
        text = ' '.join([
            '@' + self.username if self.username else '',
            self.first_name if self.first_name else '',
            self.last_name if self.last_name else ''
        ])
        return util.escape_markdown(text).encode('utf-8').decode('utf-8')

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

