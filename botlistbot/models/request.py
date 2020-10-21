from botlistbot.models import User
from botlistbot.models.basemodel import BaseModel
from peewee import *


class Request(BaseModel):
    submittant = ForeignKeyField(User)
    date = DateTimeField()
    name = CharField()
    description = TextField()
