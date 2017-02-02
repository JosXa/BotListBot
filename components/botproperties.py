import codecs

import datetime
from pprint import pprint

import emoji
import re
from telegram.error import BadRequest

from telegram import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ConversationHandler
from telegram.ext.dispatcher import run_async

import captions
import const
import helpers
import util
from const import *
from const import BotStates, CallbackActions
from custemoji import Emoji
from model import Bot, Category
from model import Category
from model import Channel
from model import Country
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
    chat_id = util.cid_from_update(update)
    countries = Country.select().order_by(Country.name).execute()

    buttons = util.build_menu([InlineKeyboardButton(
        '{} {}'.format(c.emojized, c.name),
        callback_data=util.callback_for_action(
            CallbackActions.SET_COUNTRY, {'cid': c.id, 'bid': to_edit.id})) for c in countries], 3)
    buttons.insert(0, [
        InlineKeyboardButton(captions.BACK,
                             callback_data=util.callback_for_action(CallbackActions.EDIT_BOT,
                                                                    {'id': to_edit.id})),
        InlineKeyboardButton("None",
                             callback_data=util.callback_for_action(CallbackActions.SET_COUNTRY,
                                                                    {'cid': 'None', 'bid': to_edit.id})),
    ])
    return util.send_or_edit_md_message(bot, chat_id, util.action_hint(
        "Please select a country/language for {}".format(to_edit)),
                                        to_edit=util.mid_from_update(update),
                                        reply_markup=InlineKeyboardMarkup(buttons))


@restricted
def set_description(bot, update, chat_data, to_edit=None):
    chat_id = util.cid_from_update(update)
    if to_edit:
        if to_edit.description:
            util.send_md_message(bot, chat_id, "*Current description*:\n{}".format(to_edit.description))
        util.send_action_hint(bot, chat_id, "Please send me a description to use for {} (`x` to empty)".format(to_edit))
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
        else:
            util.send_message_failure(bot, chat_id, "An unexpected error occured.")


@restricted
def set_extra(bot, update, chat_data, to_edit=None):
    chat_id = util.cid_from_update(update)
    if to_edit:
        text = (to_edit.extra + "\n\n" if to_edit.extra else '')
        text += util.action_hint("Please send me the extra text to use for {} (`x` to empty)".format(to_edit))
        util.send_md_message(bot, chat_id, text)
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
        else:
            util.send_message_failure(bot, chat_id, "An unexpected error occured.")


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
def set_name(bot, update, chat_data, to_edit=None):
    chat_id = util.cid_from_update(update)
    if to_edit:
        text = (to_edit.name + "\n\n" if to_edit.name else '')
        text += util.action_hint("Please send me a name to use for {} (`x` to empty)".format(to_edit))
        util.send_md_message(bot, chat_id, text)
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
        else:
            util.send_message_failure(bot, chat_id, "An unexpected error occured.")


@restricted
def set_username(bot, update, chat_data, to_edit=None):
    chat_id = util.cid_from_update(update)
    if to_edit:
        text = (util.escape_markdown(to_edit.username) + "\n\n" if to_edit.username else '')
        text += util.action_hint("Please send me a username for {}.".format(to_edit))
        print(text)
        util.send_md_message(bot, chat_id, text)
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
            else:
                util.send_message_failure(bot, chat_id, "An unexpected error occured.")
        else:
            util.send_message_failure(bot, chat_id, "The username you entered is not valid. Please try again...")
            return BotStates.SENDING_USERNAME


@restricted
def delete_bot_confirm(bot, update, to_edit):
    chat_id = util.cid_from_update(update)
    reply_markup = InlineKeyboardMarkup([[
        InlineKeyboardButton("Yes, delete it!", callback_data=util.callback_for_action(
            CallbackActions.DELETE_BOT, {'id': to_edit.id}
        )),
        InlineKeyboardButton(captions.BACK, callback_data=util.callback_for_action(
            CallbackActions.EDIT_BOT, {'id': to_edit.id}
        ))
    ]]
    )
    util.send_or_edit_md_message(bot, chat_id, "Are you sure?", to_edit=util.mid_from_update(update), reply_markup=reply_markup)


@restricted
def delete_bot(bot, update, to_edit):
    chat_id = util.cid_from_update(update)
    to_edit.delete_instance()
    util.send_md_message(bot, chat_id, "Bot has been deleted.")


@restricted
def accept_suggestion(bot, update, suggestion: Suggestion):
    if suggestion.action == "offline":
        suggestion.subject.offline = True
        suggestion.subject.save()
        suggestion.delete_instance()
