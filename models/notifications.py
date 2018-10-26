# -*- coding: utf-8 -*-
from peewee import *
from telegram import Chat
from models.basemodel import BaseModel


class Notifications(BaseModel):
    id = PrimaryKeyField()
    chat_id = BigIntegerField(unique=True)
    enabled = BooleanField(default=True)
    last_notification = DateField(null=True)
