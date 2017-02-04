import tokenize
from pprint import pprint
from typing import List

import emoji

from custemoji import Emoji


def results_list(args, prefix=''):
    # TODO make this method recursive
    result = '```'
    memo = emoji.emojize(':memo:', use_aliases=True)
    if isinstance(args, dict):
        for value in args.values():
            if isinstance(value, list):
                # TODO: doesnt work
                result += '\n{} '.format(memo).join(value)
            else:
                result += '\n{} {}'.format(memo, value)

    result += '```'
    return result


def success(text):
    return '{} {}'.format(Emoji.WHITE_HEAVY_CHECK_MARK, text, hide_keyboard=True)


def failure(text):
    return '{} {}'.format(Emoji.CROSS_MARK, text)


def action_hint(text):
    return '{} {}'.format(Emoji.THOUGHT_BALLOON, text)


def none_action(text):
    return '{} {}'.format(Emoji.NEGATIVE_SQUARED_CROSS_MARK, text)

