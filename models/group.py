# -*- coding: utf-8 -*-
from peewee import *
from telegram import Chat
from models.basemodel import BaseModel


class Group(BaseModel):
    id = PrimaryKeyField()
    chat_id = IntegerField(unique=True)
    title = CharField()

    @staticmethod
    def from_telegram_object(group: Chat):
        try:
            u = Group.get(Group.chat_id == group.id)
        except Group.DoesNotExist:
            u = Group(chat_id=group.id, title=group.title)
            u.save()
        return u
