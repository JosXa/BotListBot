# -*- coding: utf-8 -*-
from peewee import *

from botlistbot.models import Bot
from botlistbot.models.basemodel import BaseModel


class Message(BaseModel):
    message_id = PrimaryKeyField()
    chat_id = IntegerField(unique=True)
    command = CharField(choices=['offline', 'spam', 'new'])
    entity = ForeignKeyField(Bot)

    @staticmethod
    def get_or_create(telegram_message, command, entity: Bot):
        try:
            u = Message.get(Message.message_id == telegram_message.message_id)
        except Message.DoesNotExist:
            u = Message(message_id=telegram_message.message_id, chat_id=telegram_message.chat.id, entity=entity,
                        command=command)
            u.save()
        return u
