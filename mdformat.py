import json
import tokenize
from pprint import pprint
from typing import List

import emoji

from custemoji import Emoji

MAX_LINE_CHARACTERS = 31


def smallcaps(text):
    SMALLCAPS_CHARS = 'ᴀʙᴄᴅᴇғɢʜɪᴊᴋʟᴍɴᴏᴘǫʀsᴛᴜᴠᴡxʏᴢ'
    lowercase_ord = 96
    uppercase_ord = 64

    result = ''
    for i in text:
        index = ord(i)
        if 122 >= index >= 97:
            result += SMALLCAPS_CHARS[index - lowercase_ord - 1]
        elif 90 >= index >= 65:
            result += SMALLCAPS_CHARS[index - uppercase_ord - 1]
        elif index == 32:
            result += ' '

    return result


def strikethrough(text: str):
    SPEC = '̶'
    return ''.join([x + SPEC if x != ' ' else ' ' for x in text])


def results_list(args, prefix=''):
    # TODO make this method recursive
    result = '```'
    memo = emoji.emojize(':memo:', use_aliases=True)
    if isinstance(args, dict):
        for value in args.values():
            if isinstance(value, list):
                # TODO: doesnt work
                for s in value:
                    result += '\n{} {}'.format(memo, s)
            else:
                result += '\n{} {}'.format(memo, value)

    result += '```'
    return result


def number_as_emoji(n):
    EMOJI_NUMBERS = '0️⃣1️⃣2️⃣3️⃣4️⃣5️⃣6️⃣7️⃣8️⃣9️⃣'
    idx = str(n)
    result = []

    for char in idx:
        i = (int(char)) * 3
        # if i == 1:
        #     i -= 1
        result += EMOJI_NUMBERS[i: i + 3]

    return ''.join(result)


def centered(text):
    result = '\n'.join([line.center(MAX_LINE_CHARACTERS) for line in text.splitlines()])
    return result


def success(text):
    return '{} {}'.format(Emoji.WHITE_HEAVY_CHECK_MARK, text, hide_keyboard=True)


def love(text):
    return '💖 {}'.format(text, hide_keyboard=True)


def failure(text):
    return '{} {}'.format(Emoji.CROSS_MARK, text)


def action_hint(text):
    return '{} {}'.format(Emoji.THOUGHT_BALLOON, text)


def none_action(text):
    return '{} {}'.format(Emoji.NEGATIVE_SQUARED_CROSS_MARK, text)


if __name__ == '__main__':
    # test = json.loads('{"category": ["Miscellaneous"], \
    #            "intro_es": "Spanish intro sent", \
    # "new_bots_list": "List of new bots sent"}')
    # print(results_list(test))
    print(centered('• @botlist •\n03-02-2017'))
