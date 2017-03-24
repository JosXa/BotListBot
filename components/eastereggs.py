import random
from pprint import pprint

from telegram import KeyboardButton

import captions


def _crapPy_Tr0ll_kbmarkup(admin=False):
    first = ['gay', 'pony', 'sack', 'telegram']
    second = ['tales', 'porn', 'rice', 'bugs']
    buttons = [
        [KeyboardButton(random.choice(a)) for a in first],
        [KeyboardButton(random.choice(b)) for b in second]
    ]

    # buttons = [
    #     [KeyboardButton(captions.CATEGORIES)],
    #     [KeyboardButton(captions.NEW_BOTS), KeyboardButton(captions.SEARCH)],
    #     [KeyboardButton(captions.CONTRIBUTING), KeyboardButton(captions.EXAMPLES)],
    #     [KeyboardButton(captions.HELP)],
    # ]

    if admin:
        buttons.insert(1, [KeyboardButton(captions.ADMIN_MENU)])
    return buttons
