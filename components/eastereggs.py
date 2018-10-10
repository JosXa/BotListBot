import random

from peewee import fn

import util
from flow.context import FlowContext
from models import Bot
from models import track_activity
from telegram import KeyboardButton
from telegram import ReplyKeyboardMarkup, Update


@track_activity('easteregg', '"crappy troll markup"')
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


def send_next(update: Update, context: FlowContext):
    uid = update.effective_user.id
    rows = None
    if context.args:
        try:
            rows = int(context.args[0])
        except:
            rows = None
    reply_markup = ReplyKeyboardMarkup(_crapPy_Tr0ll_kbmarkup(rows), one_time_keyboard=True, per_user=True)
    text = 'ɹoʇɐɹǝuǝb ǝɯɐuɹǝsn ɯɐɹbǝןǝʇ'
    util.send_md_message(context.bot, uid, text, reply_markup=reply_markup)


def send_random_bot(bot, update):
    from components.explore import send_bot_details
    random_bot = Bot.select().where((Bot.approved == True, Bot.disabled == False), (Bot.description.is_null(
        False))).order_by(fn.Random()).limit(1)[0]
    send_bot_details(bot, update, random_bot)
