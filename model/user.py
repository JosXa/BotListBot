import datetime
from pprint import pprint

from playhouse.sqlite_ext import JSONField

import const
import util
from model.category import Category
from model.basemodel import BaseModel
from peewee import *

from model.country import Country
from telegram import User as TelegramUser
from telegram import UserProfilePhotos


class User(BaseModel):
    id = PrimaryKeyField()
    chat_id = IntegerField()
    username = CharField(null=True)
    first_name = CharField(null=True)
    last_name = CharField(null=True)
    photo = CharField(null=True)

    @staticmethod
    def from_telegram_object(user: TelegramUser):
        print(user.type)
        try:
            u = User.get(User.chat_id == user.id)
        except User.DoesNotExist:
            photos = user.get_profile_photos().photos

            photo = None
            # TODO: xxx
            try:
                if photos.total_count > 0:
                    photo = photos[-1]
            except AttributeError:
                pass

            u = User(chat_id=user.id, username=user.username, first_name=user.first_name, last_name=user.last_name,
                     photo=photo)
            u.save()
        return u
