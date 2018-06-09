import json
import logging
import re
import time
import traceback
from collections import OrderedDict
from functools import partial
from functools import wraps
from pprint import pprint
from typing import List

import const
import settings
from custemoji import Emoji
from telegram import ChatAction
from telegram import ParseMode
from telegram import TelegramError, ReplyKeyboardRemove
from telegram.error import BadRequest


def stop_banned(update, user):
    if user.banned:
        update.message.reply_text(failure("Sorry, but you are banned from contributing."))
        return True
    return False


def track_groups(func):
    from models.group import Group
    """
    Decorator that stores all groups that the bot has been added to
    """

    @wraps(func)
    def wrapped(bot, update, *args, **kwargs):
        try:
            if update.effective_chat.type == 'group':
                Group.from_telegram_object(update.effective_chat)
        except (NameError, AttributeError):
            try:
                if update.message.new_chat_members[0].id == settings.SELF_BOT_ID:
                    Group.from_telegram_object(update.callback_query.message.chat)
            except (NameError, AttributeError):
                logging.error("No chat_id available in update for track_groups.")
        return func(bot, update, *args, **kwargs)

    return wrapped


def restricted(func=None, strict=False, silent=False):
    if func is None:
        # If called without method, we've been called with optional arguments.
        # We return a decorator with the optional arguments filled in.
        return partial(restricted, strict=strict, silent=silent)

    @wraps(func)
    def wrapped(bot, update, *args, **kwargs):
        chat_id = update.effective_user.id

        if chat_id not in settings.MODERATORS:
            try:
                print("Unauthorized access denied for {}.".format(chat_id))
                if not silent:
                    bot.sendPhoto(chat_id, open('assets/img/go_away_noob.png', 'rb'),
                                  caption="Moderator Area. Unauthorized.")
                return
            except (TelegramError, AttributeError):
                return

        if strict and chat_id not in settings.ADMINS:
            if not silent:
                bot.sendMessage(chat_id, "This function is restricted to the channel creator.")
            return

        return func(bot, update, *args, **kwargs)

    return wrapped


def private_chat_only(func):
    @wraps(func)
    def wrapped(bot, update, *args, **kwargs):
        if update.effective_chat.type == 'private':
            return func(bot, update, *args, **kwargs)
        else:
            # not private
            pass

    return wrapped


def timeit(method):
    def timed(*args, **kw):
        ts = time.time()
        result = method(*args, **kw)
        te = time.time()

        print('%r (%r, %r) %2.2f sec' % (method.__name__, args, kw, te - ts))
        return result

    return timed


def build_menu(buttons: List,
               n_cols,
               header_buttons: List = None,
               footer_buttons: List = None):
    menu = list()
    for i in range(0, len(buttons)):
        item = buttons[i]
        if i % n_cols == 0:
            menu.append([item])
        else:
            menu[int(i / n_cols)].append(item)
    if header_buttons:
        menu.insert(0, header_buttons)
    if footer_buttons:
        menu.append(footer_buttons)
    return menu


def cid_from_update(update):
    return update.effective_chat.id


def uid_from_update(update):
    return update.effective_user.id


# def deep_link_action_url(action: object, params: Dict = None) -> object:
#     callback_data = {'a': action}
#     if params:
#         for key, value in params.items():
#             callback_data[key] = value
#     # s = urllib.parse.urlencode(callback_data)
#     s = callback_str_from_dict(callback_data)
#     print(s)
#     return s


def encode_base64(query):
    return re.sub(r'[^a-zA-Z0-9+/]', '', query)


def callback_for_action(action, params=None):
    """
    Generates an uglified JSON representation to use in ``callback_data`` of ``InlineKeyboardButton``.
    :param action: The identifier for your action.
    :param params: A dict of additional parameters.
    :return:
    """

    if params is None:
        params = dict()

    callback_data = {'a': action}
    if params:
        for key, value in params.items():
            callback_data[key] = value
    return callback_str_from_dict(callback_data)


def callback_data_from_update(update):
    try:
        data = update.callback_query.data
        return json.loads(data)
    except:
        return {}


def is_group_message(update):
    try:
        return update.effective_message.chat.type in ['group', 'supergroup']
    except (NameError, AttributeError):
        try:
            return update.message.new_chat_members[0].id == settings.SELF_BOT_ID
        except (NameError, AttributeError):
            return False


def is_private_message(update):
    return update.effective_message.chat.type == 'private'


def original_reply_id(update):
    try:
        return update.message.reply_to_message.message_id
    except (NameError, AttributeError):
        return None


def is_inline_message(update):
    try:
        im_id = update.callback_query.inline_message_id
        if im_id and im_id != '':
            return True
        else:
            return False
    except (NameError, AttributeError):
        return False


def message_text_from_update(update):
    try:
        return update.message.text
    except (NameError, AttributeError):
        try:
            return update.callback_query.message.text
        except (NameError, AttributeError):
            return None


def mid_from_update(update):
    try:
        return update.callback_query.message.message_id
    except (NameError, AttributeError):
        try:
            message_id = update.callback_query.inline_message_id
            return message_id if message_id != '' else None
        except (NameError, AttributeError):
            return None


def escape_markdown(text):
    """Helper function to escape telegram markup symbols"""
    escape_chars = '\*_`\['
    return re.sub(r'([%s])' % escape_chars, r'\\\1', text)


def callback_str_from_dict(d):
    dumped = json.dumps(d, separators=(',', ':'))
    assert len(dumped) <= 64
    return dumped


def wait(bot, update, t=1.5):
    chat_id = uid_from_update(update)
    bot.sendChatAction(chat_id, ChatAction.TYPING)
    time.sleep(t)


def order_dict_lexi(d):
    res = OrderedDict()
    for k, v in sorted(d.items()):
        if isinstance(v, dict):
            res[k] = order_dict_lexi(v)
        else:
            res[k] = v
    return res


def private_or_else_group_message(bot, chat_id, text):
    pass


def send_or_edit_md_message(bot, chat_id, text, to_edit=None, **kwargs):
    try:
        if to_edit:
            return bot.edit_message_text(text, chat_id=chat_id, message_id=to_edit, parse_mode=ParseMode.MARKDOWN,
                                         **kwargs)

        return send_md_message(bot, chat_id, text=text, **kwargs)
    except BadRequest as e:
        if 'not modified' in e.message.lower():
            logging.debug('Message not modified.')
            pass
        else:
            traceback.print_exc()


def send_md_message(bot, chat_id, text: str, **kwargs):
    if 'disable_web_page_preview' not in kwargs:
        kwargs['disable_web_page_preview'] = True
    return bot.sendMessage(chat_id, text, parse_mode=ParseMode.MARKDOWN, **kwargs)


def send_message_success(bot, chat_id, text: str, add_punctuation=True, reply_markup=None, **kwargs):
    if add_punctuation:
        if text[-1] != '.':
            text += '.'

    if not reply_markup:
        reply_markup = ReplyKeyboardRemove()
    return bot.sendMessage(chat_id, success(text), parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True,
                           reply_markup=reply_markup,
                           **kwargs)


def send_message_failure(bot, chat_id, text: str, **kwargs):
    text = str.strip(text)
    if text[-1] != '.':
        text += '.'
    return bot.sendMessage(chat_id, failure(text), parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True,
                           **kwargs)


def send_action_hint(bot, chat_id, text: str, **kwargs):
    if text[-1] == '.':
        text = text[0:-1]
    return bot.sendMessage(chat_id, action_hint(text), parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True,
                           **kwargs)


def success(text):
    return '{} {}'.format(Emoji.WHITE_HEAVY_CHECK_MARK, text, hide_keyboard=True)


def failure(text):
    return '{} {}'.format(Emoji.CROSS_MARK, text)


def action_hint(text):
    return '💬 {}'.format(text)
