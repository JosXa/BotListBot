# -*- coding: utf-8 -*-
from typing import Set

from peewee import *

from model.basemodel import BaseModel
from model.bot import Bot


class Keyword(BaseModel):
    id = PrimaryKeyField()
    name = CharField()
    entity = ForeignKeyField(Bot)

    def __str__(self):
        return '#' + self.name

    @classmethod
    def get_distinct_names(cls, exclude_from_bot: Bot, exclude_suggestions=True) -> Set[str]:
        exclude_kw = {x.name for x in exclude_from_bot.keywords}
        if exclude_suggestions:
            suggestions = KeywordSuggestion.select(KeywordSuggestion.name).where(
                KeywordSuggestion.entity == exclude_from_bot,
            ).distinct()
            exclude_kw.update(suggestions)
        return {x.name for x in
                cls.select(cls.name).distinct().where(Keyword.name.not_in(exclude_kw))}


class KeywordSuggestion(BaseModel):
    id = PrimaryKeyField()
    name = CharField()
    entity = ForeignKeyField(Bot)

    def __str__(self):
        return '#' + self.name

