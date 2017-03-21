# -*- coding: utf-8 -*-
import codecs

import datetime
from pprint import pprint

import emoji
import re
from telegram.error import BadRequest

from model import User
from telegram import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ConversationHandler
from telegram.ext.dispatcher import run_async

import captions
import const
import helpers
import messages
import util
from const import *
from const import BotStates, CallbackActions
from custemoji import Emoji
from model import Bot, Category
from model import Category
from model import Channel
from model import Country
from model import Keyword
from model import Suggestion
from util import restricted

"""
Edit every bot property except for category
"""

CLEAR_QUERY = "x"


def _is_clear_query(query):
    return query.lower() == CLEAR_QUERY


@restricted
def set_country(bot, update, to_edit):
    uid = util.uid_from_update(update)
    countries = Country.select().order_by(Country.name).execute()

    buttons = util.build_menu(
        [InlineKeyboardButton(
            '{} {}'.format(c.emojized, c.name),
            callback_data=util.callback_for_action(
                CallbackActions.SET_COUNTRY, {'cid': c.id, 'bid': to_edit.id})) for c in countries
         ], 3)
    buttons.insert(0, [
        InlineKeyboardButton(captions.BACK,
                             callback_data=util.callback_for_action(CallbackActions.EDIT_BOT,
                                                                    {'id': to_edit.id})),
        InlineKeyboardButton("None",
                             callback_data=util.callback_for_action(CallbackActions.SET_COUNTRY,
                                                                    {'cid': 'None', 'bid': to_edit.id})),
    ])
    return util.send_or_edit_md_message(bot, uid, util.action_hint(
        "Please select a country/language for {}".format(to_edit)),
                                        to_edit=util.mid_from_update(update),
                                        reply_markup=InlineKeyboardMarkup(buttons))


@restricted
def set_description(bot, update, chat_data, to_edit=None):
    uid = util.uid_from_update(update)
    if to_edit:
        util.send_action_hint(bot, uid, "Please send me a description to use for {}. `x` to drop | /cancel".format(
            to_edit.username))
        chat_data['edit_bot'] = to_edit
        return BotStates.SENDING_DESCRIPTION
    elif update.message:
        text = update.message.text
        to_edit = chat_data.get('edit_bot', None)
        if to_edit:
            if _is_clear_query(text):
                to_edit.description = None
            else:
                to_edit.description = text
            to_edit.save()
            from components.admin import edit_bot
            edit_bot(bot, update, chat_data, to_edit)
            return ConversationHandler.END
        else:
            util.send_message_failure(bot, uid, "An unexpected error occured.")


@restricted
def set_extra(bot, update, chat_data, to_edit=None):
    uid = util.uid_from_update(update)
    if to_edit:
        text = (to_edit.extra + "\n\n" if to_edit.extra else '')
        text += util.action_hint("Please send me the extra text to use for {}. `x` to drop".format(to_edit.username))
        util.send_md_message(bot, uid, text)
        chat_data['edit_bot'] = to_edit
        return BotStates.SENDING_EXTRA
    elif update.message:
        text = update.message.text
        to_edit = chat_data.get('edit_bot', None)
        if to_edit:
            if _is_clear_query(text):
                to_edit.extra = None
            else:
                to_edit.extra = text
            to_edit.save()
            from components.admin import edit_bot
            edit_bot(bot, update, chat_data, to_edit)
            return ConversationHandler.END
        else:
            util.send_message_failure(bot, uid, "An unexpected error occured.")


@restricted
def toggle_inlinequeries(bot, update, to_edit):
    to_edit.inlinequeries = not to_edit.inlinequeries
    to_edit.save()


@restricted
def toggle_official(bot, update, to_edit):
    to_edit.official = not to_edit.official
    to_edit.save()


@restricted
def toggle_offline(bot, update, to_edit):
    to_edit.offline = not to_edit.offline
    to_edit.save()


@restricted
def toggle_spam(bot, update, to_edit):
    to_edit.spam = not to_edit.spam
    to_edit.save()


@restricted
def set_name(bot, update, chat_data, to_edit=None):
    uid = util.uid_from_update(update)
    if to_edit:
        text = (to_edit.name + "\n\n" if to_edit.name else '')
        text += util.action_hint("Please send me a name to use for {}. `x` to drop".format(to_edit.username))
        util.send_md_message(bot, uid, text)
        chat_data['edit_bot'] = to_edit
        return BotStates.SENDING_NAME
    elif update.message:
        text = update.message.text
        to_edit = chat_data.get('edit_bot', None)
        if to_edit:
            if _is_clear_query(text):
                to_edit.name = None
            else:
                to_edit.name = text
            to_edit.save()
            from components.admin import edit_bot
            edit_bot(bot, update, chat_data, to_edit)
            return ConversationHandler.END
        else:
            util.send_message_failure(bot, uid, "An unexpected error occured.")


@restricted
def set_username(bot, update, chat_data, to_edit=None):
    uid = util.uid_from_update(update)
    if to_edit:
        text = (util.escape_markdown(to_edit.username) + "\n\n" if to_edit.username else '')
        text += util.action_hint("Please send me a username for {}.".format(to_edit))
        util.send_md_message(bot, uid, text)
        chat_data['edit_bot'] = to_edit
        return BotStates.SENDING_USERNAME
    elif update.message:
        text = update.message.text
        username = helpers.validate_username(text)
        if username:
            to_edit = chat_data.get('edit_bot', None)
            if to_edit:
                to_edit.username = username
                to_edit.save()
                from components.admin import edit_bot
                edit_bot(bot, update, chat_data, to_edit)
                return ConversationHandler.END
            else:
                util.send_message_failure(bot, uid, "An unexpected error occured.")
        else:
            util.send_message_failure(bot, uid, "The username you entered is not valid. Please try again...")
            return BotStates.SENDING_USERNAME


@restricted
def set_keywords_init(bot, update, chat_data, to_edit):
    chat_data['set_keywords_msg'] = util.mid_from_update(update)
    return set_keywords(bot, update, chat_data, to_edit)


@restricted
def set_keywords(bot, update, chat_data, to_edit):
    chat_id = util.uid_from_update(update)
    keywords = Keyword.select().where(Keyword.entity == to_edit)
    chat_data['edit_bot'] = to_edit
    set_keywords_msgid = chat_data.get('set_keywords_msg')

    kw_remove_buttons = [InlineKeyboardButton('{} ✖️'.format(x),
                                              callback_data=util.callback_for_action(CallbackActions.REMOVE_KEYWORD,
                                                                                     {'id': to_edit.id, 'kwid': x.id}))
                         for x in keywords]
    buttons = util.build_menu(kw_remove_buttons, 2, header_buttons=[
        InlineKeyboardButton(captions.DONE,
                             callback_data=util.callback_for_action(CallbackActions.ABORT_SETTING_KEYWORDS,
                                                                    {'id': to_edit.id}))
    ])
    reply_markup = InlineKeyboardMarkup(buttons)
    msg = util.send_or_edit_md_message(bot,
                                       chat_id,
                                       util.action_hint('Send me the keywords for {} one by one...\n\n{}'.format(
                                           util.escape_markdown(to_edit.username), messages.KEYWORD_BEST_PRACTICES)),
                                       to_edit=set_keywords_msgid,
                                       reply_markup=reply_markup)
    chat_data['set_keywords_msg'] = msg.message_id
    return BotStates.SENDING_KEYWORDS


@restricted
def add_keyword(bot, update, chat_data):
    kw = update.message.text
    bot_to_edit = chat_data.get('edit_bot')
    kw = helpers.format_keyword(kw)
    if len(kw) <= 2:
        update.message.reply_text('Keywords must be longer than 2 characters.')
        return
    if len(kw) >= 20:
        update.message.reply_text('Keywords must not be longer than 20 characters.')

    # ignore duplicates
    try:
        Keyword.get((Keyword.name == kw) & (Keyword.entity == bot_to_edit))
        return
    except Keyword.DoesNotExist:
        pass
    kw_obj = Keyword(name=kw, entity=bot_to_edit)
    kw_obj.save()
    set_keywords(bot, update, chat_data, bot_to_edit)


@restricted
def delete_bot_confirm(bot, update, to_edit):
    chat_id = util.uid_from_update(update)
    reply_markup = InlineKeyboardMarkup([[
        InlineKeyboardButton("Yes, delete it!", callback_data=util.callback_for_action(
            CallbackActions.DELETE_BOT, {'id': to_edit.id}
        )),
        InlineKeyboardButton(captions.BACK, callback_data=util.callback_for_action(
            CallbackActions.EDIT_BOT, {'id': to_edit.id}
        ))
    ]]
    )
    util.send_or_edit_md_message(bot, chat_id, "Are you sure?", to_edit=util.mid_from_update(update),
                                 reply_markup=reply_markup)


@restricted
def delete_bot(bot, update, to_edit):
    chat_id = util.uid_from_update(update)
    to_edit.delete_instance()
    util.send_or_edit_md_message(bot, chat_id, "Bot has been deleted.", to_edit=util.mid_from_update(update))


def change_category(bot, update, to_edit, category):
    uid = util.uid_from_update(update)
    user = User.get(User.chat_id == uid)
    if uid == 62056065:
        sugg = Suggestion(user=user, action='change_category', date=datetime.date.today(), subject=to_edit,
                          value=category.id)
        sugg.save()
    else:
        to_edit.category = category
        to_edit.save()
