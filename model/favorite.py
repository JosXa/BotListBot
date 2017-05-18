# -*- coding: utf-8 -*-
import datetime
from typing import List

from peewee import *

import helpers
import util
from model import Bot
from model.basemodel import BaseModel
from model.category import Category
from model.country import Country
from model.user import User


class Favorite(BaseModel):
    id = PrimaryKeyField()
    user = ForeignKeyField(User)
    bot = ForeignKeyField(Bot, null=True)
    custom_bot = CharField(null=True)
    date_added = DateField()

    CUSTOM_CATEGORY = Category(id=1000, order=1000, emojis='👤', name='Others')

    @staticmethod
    def add(user, item: Bot):
        """
        :return: Tuple of (Favorite, created: Boolean)
        """
        try:
            fav = Favorite.get(Favorite.bot == item, Favorite.user == user)
            return fav, False
        except Favorite.DoesNotExist:
            fav = Favorite(user=user, bot=item, date_added=datetime.date.today())
            fav.save()
            return fav, True

    @staticmethod
    def select_all(user):
        user_favs = list(Favorite.select().where(Favorite.user == user))
        for n, f in enumerate(user_favs):
            if f.bot is None:
                bot = Bot(category=Favorite.CUSTOM_CATEGORY, username=f.custom_bot, approved=True,
                          date_added=datetime.date.today())
                f.bot = bot
                user_favs[n] = f
            if f.bot.category is None:
                f.bot.category = Favorite.CUSTOM_CATEGORY
        return user_favs

    @staticmethod
    def get_oldest(user):
        return Favorite.select().where(Favorite.user == user).order_by(Favorite.date_added).first()
