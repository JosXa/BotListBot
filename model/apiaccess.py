# -*- coding: utf-8 -*-
from peewee import *
from telegram import User as TelegramUser
import util
from model.user import User
from model.basemodel import BaseModel


class APIAccess(BaseModel):
    user = ForeignKeyField(User)
    token = CharField(32)
    webhook_url = CharField(null=True)

