import random
from pprint import pprint

from telegram import ReplyKeyboardMarkup

import util
from telegram import KeyboardButton

import captions


def _crapPy_Tr0ll_kbmarkup(rows=None):
    if rows is None:
        rows = 4
    first = ['Gay', 'Pony', 'Dick', 'Telegram', 'Milk', 'WhatsApp', 'Daniils', 'T3CHNOs', 'Adult', 'ThirdWorld',
             'Asian', 'Mexican', 'SM', 'Russian', 'Chinese', 'Gonzo', 'Anime']
    second = ['Tales', 'Porn', 'Rice', 'Bugs', 'Whores', 'Pigs', 'Alternatives', 'Pics', 'Penetrator', 'Addiction',

              'Ducks', 'Slaves']
    third = ['Collection', 'Channel', 'Bot', 'Radio', 'Chat', 'Discuss ion', 'Conversation', 'Voting', 'ForPresident']

    def compound():
        choices = [
            '{} {} {}'.format(random.choice(first), random.choice(second), random.choice(third)),
            '@{}{}{}'.format(random.choice(first), random.choice(second), ''.join(random.choice(third).split(' '))),
        ]
        return random.choice(choices)

    buttons = [[KeyboardButton(compound()) for x in range(2)] for y in range(rows)]
    return buttons


def send_next(bot, update, args=None):
    uid = util.uid_from_update(update)
    rows = None
    if args:
        try:
            rows = int(args[0])
        except:
            rows = None
    reply_markup = ReplyKeyboardMarkup(_crapPy_Tr0ll_kbmarkup(rows), one_time_keyboard=True, per_user=True)
    text = 'ɹoʇɐɹǝuǝb ǝɯɐuɹǝsn ɯɐɹbǝןǝʇ'
    util.send_md_message(bot, uid, text, reply_markup=reply_markup)
