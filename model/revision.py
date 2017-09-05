# -*- coding: utf-8 -*-
from functools import lru_cache

from peewee import *

from model.basemodel import BaseModel


class Revision(BaseModel):
    nr = IntegerField(default=1)
    _instance = None

    @property
    def next(self):
        return self.nr + 1

    @staticmethod
    def get_instance():
        if not Revision._instance:
            selection = list(Revision.select())
            assert len(selection) == 1
            Revision._instance = selection[0]
        return Revision._instance
