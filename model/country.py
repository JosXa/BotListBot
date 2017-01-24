from peewee import *

from model.basemodel import BaseModel


class Country(BaseModel):
    id = PrimaryKeyField()
    name = CharField(unique=True)
    emoji = CharField()
