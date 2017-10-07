# -*- coding: utf-8 -*-
import datetime

import logging
from peewee import *
from telegram import Update

import helpers
import util
from model import User
from model.basemodel import BaseModel


def track_activity(action: str, entity: str = None, level: int = logging.INFO):
    def decorator(func):
        def wrapped(bot, update, *args, **kwargs):
            result = func(bot, update, *args, **kwargs)
            Statistic.of(update, action, entity, level)
            return result

        return wrapped

    return decorator


class Statistic(BaseModel):
    IMPORTANT = 30
    WARN = logging.WARNING
    INFO = logging.INFO
    ANALYSIS = logging.DEBUG
    DETAILED = 9

    ACTIONS = {
        'search': 'searched for',
        'button-press': 'clicked on',
        'command': 'executed command',
        'chosen-inlinequery-result': 'sent an inline query',
        'inlinequery': 'did an inline query: ',
        'menu': 'entered menu',
        'error': 'received error',
        'share': 'shared',
        'accept': 'accepted',
        'request': 'requested',
        'reject': 'rejected',
        'ban': 'banned',
        'unban': 'unbanned',
        'apply': 'applied changes to',
        'remove': 'removed',
        'send': 'sent',
        'delete': 'deleted',
        'suggestion': 'made a suggestion to',
        'easteregg': 'tried out the easteregg',
        'explore': 'explored',
        'view-details': 'viewed details of',
        'add-favorite': 'added a new favorite:',
        'view-favorites': 'viewed their favorites',
    }
    user = ForeignKeyField(User)
    date = DateTimeField()
    action = CharField()
    entity = CharField(null=True)
    level = SmallIntegerField(default=logging.INFO)

    EMOJIS = {
        IMPORTANT: '🔴',
        WARN: '🔺',
        INFO: '⚪️',
        ANALYSIS: '▫️',
        DETAILED: '▪️'
    }

    @staticmethod
    def collect_recent(limit=400, min_level=logging.INFO):
        return Statistic.select().where(Statistic.level >= min_level).limit(limit)

    @staticmethod
    def collect_all_as_file():
        pass  # TODO

    def __get_action_text(self):
        text = self.ACTIONS.get(self.action)
        return text if text else self.action

    def __format_entity(self):
        if self.action == 'command':
            return '/' + self.entity
        if self.action == 'menu':
            return util.escape_markdown(self.entity.title())
        return util.escape_markdown(self.entity)


    @classmethod
    def of(cls, issuer, action: str, entity: str = None, level=logging.INFO):
        # if action not in Statistic.ACTIONS.keys():
        #     raise ValueError('"{}" is not a valid action. Refer to Statistic.ACTIONS for available keys.')

        if isinstance(issuer, User):
            user = issuer
        elif isinstance(issuer, Update):
            user = User.from_update(issuer)
        else:
            raise AttributeError("The issuer argument needs to be an object of type User or Update.")
        obj = cls(user=user, date=datetime.datetime.now(), action=action, entity=entity, level=level)
        obj.save()
        return obj

    def md_str(self, no_date=False):
        return '{} {}{} _{}_{}.'.format(
            self.EMOJIS[self.level],
            '' if no_date else '{}: '.format(helpers.slang_datetime(self.date)),
            self.user.markdown_short,
            self.__get_action_text(),
            ' ' + self.__format_entity() if self.entity else ''
        )
