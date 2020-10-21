# -*- coding: utf-8 -*-
from peewee import *
from typing import Set

from botlistbot.models.basemodel import BaseModel
from botlistbot.models.bot import Bot


class Keyword(BaseModel):
    id = PrimaryKeyField()
    name = CharField()
    entity = ForeignKeyField(Bot)

    class Meta:
        indexes = (
            (('entity', 'name'), True),  # Note the trailing comma!
        )

    def __str__(self):
        return '#' + self.name

    @classmethod
    def get_distinct_names(cls, exclude_from_bot: Bot, exclude_suggestions=True) -> Set[str]:
        exclude_kw = {x.name for x in exclude_from_bot.keywords}
        return {x.name for x in
                cls.select(cls.name).distinct().where(Keyword.name.not_in(exclude_kw))}
