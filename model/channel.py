# -*- coding: utf-8 -*-
from peewee import *

from model.basemodel import BaseModel


class Channel(BaseModel):
    chat_id = IntegerField()
    username = CharField()
    last_update = DateField(null=True)

    # message ids
    intro_en_mid = IntegerField(default=1)
    intro_es_mid = IntegerField(default=1)
    new_bots_mid = IntegerField(default=1)
    category_list_mid = IntegerField(default=1)
    footer_mid = IntegerField(default=1)


