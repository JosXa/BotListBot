# -*- coding: utf-8 -*-
from peewee import *
from telegram import User as TelegramUser
import util
from models.user import User
from models.basemodel import BaseModel


class APIAccess(BaseModel):
    user = ForeignKeyField(User)
    token = CharField(64)
    webhook_url = CharField(null=True)

