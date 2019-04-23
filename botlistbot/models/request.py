from models import User
from models.basemodel import BaseModel
from peewee import *


class Request(BaseModel):
    submittant = ForeignKeyField(User)
    date = DateTimeField()
    name = CharField()
    description = TextField()
