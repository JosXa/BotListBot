from peewee import *

from model.basemodel import BaseModel


class Channel(BaseModel):
    chat_id = IntegerField()
    username = CharField()

    # message ids
    intro_mid = IntegerField(default=1)
    new_bots_mid = IntegerField(default=1)
    category_list_mid = IntegerField(default=1)


