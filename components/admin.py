# -*- coding: utf-8 -*-
import logging
import re
from pprint import pprint

import emoji
from telegram import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup

import captions
import mdformat
import util
from const import *
from const import BotStates, CallbackActions
from custemoji import Emoji
from model import Bot
from model import Category
from model import Suggestion
from util import restricted

logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.INFO)
log = logging.getLogger(__name__)


@restricted
def menu(bot, update):
    chat_id = util.uid_from_update(update)

    buttons = _admin_buttons()

    util.send_md_message(bot, chat_id, "Administration menu.",
                         reply_markup=ReplyKeyboardMarkup(buttons, resize_keyboard=True))
    return BotStates.ADMIN_MENU


def _admin_buttons():
    n_unapproved = len(Bot.select().where(Bot.approved == False))
    n_suggestions = len(Suggestion.select())

    first_row = list()
    if n_unapproved > 0:
        first_row.append(KeyboardButton(captions.APPROVE_BOTS + ' ({} 🆕)'.format(n_unapproved)))
    if n_suggestions > 0:
        first_row.append(KeyboardButton(captions.APPROVE_SUGGESTIONS + ' ({})'.format(n_suggestions)))

    buttons = [[
        KeyboardButton(captions.SEND_BOTLIST)
    ], [
        KeyboardButton(captions.FIND_OFFLINE),
        KeyboardButton(captions.SEND_CONFIG_FILES)
    ]]

    if len(first_row) > 0:
        buttons.insert(0, first_row)

    return buttons


@restricted
def _input_failed(bot, update, chat_data, text):
    chat_id = util.uid_from_update(update)
    util.send_message_failure(bot, chat_id, text)
    chat_data['add_bot_message'] = None


def _add_bot_to_chatdata(chat_data, category=None):
    new_bot = Bot(category=category)
    chat_data['add_bot'] = new_bot


def _edit_bot_buttons(to_edit: Bot):
    bid = {'id': to_edit.id}
    buttons = [
        InlineKeyboardButton(to_edit.name if to_edit.name else "Set Name", callback_data=util.callback_for_action(
            CallbackActions.EDIT_BOT_NAME, bid
        )),
        InlineKeyboardButton(to_edit.username, callback_data=util.callback_for_action(
            CallbackActions.EDIT_BOT_USERNAME, bid
        )),
        InlineKeyboardButton(str(to_edit.category), callback_data=util.callback_for_action(
            CallbackActions.EDIT_BOT_SELECT_CAT, bid
        )),
        InlineKeyboardButton("Change description" if to_edit.description else "Write a description",
                             callback_data=util.callback_for_action(
                                 CallbackActions.EDIT_BOT_DESCRIPTION, bid
                             )),
        InlineKeyboardButton(to_edit.country.emojized if to_edit.country else "Set country/language",
                             callback_data=util.callback_for_action(CallbackActions.EDIT_BOT_COUNTRY, bid)),
        InlineKeyboardButton("Change extra text" if to_edit.extra else "Add an extra text",
                             callback_data=util.callback_for_action(
                                 CallbackActions.EDIT_BOT_EXTRA, bid
                             )),
    ]

    # inlinequeries
    if to_edit.inlinequeries:
        buttons.append(
            InlineKeyboardButton("🔎 {}".format(Emoji.WHITE_HEAVY_CHECK_MARK), callback_data=util.callback_for_action(
                CallbackActions.EDIT_BOT_INLINEQUERIES, {'id': to_edit.id, 'value': False}
            )))
    else:
        buttons.append(
            InlineKeyboardButton("🔎 {}".format(Emoji.HEAVY_MULTIPLICATION_X), callback_data=util.callback_for_action(
                CallbackActions.EDIT_BOT_INLINEQUERIES, {'id': to_edit.id, 'value': True}
            )))

    # official
    if to_edit.official:
        buttons.append(
            InlineKeyboardButton("🔹 {}".format(Emoji.WHITE_HEAVY_CHECK_MARK), callback_data=util.callback_for_action(
                CallbackActions.EDIT_BOT_OFFICIAL, {'id': to_edit.id, 'value': False}
            )))
    else:
        buttons.append(
            InlineKeyboardButton("🔹 {}".format(Emoji.HEAVY_MULTIPLICATION_X), callback_data=util.callback_for_action(
                CallbackActions.EDIT_BOT_OFFICIAL, {'id': to_edit.id, 'value': True}
            )))

    # offline
    if to_edit.offline:
        buttons.append(
            InlineKeyboardButton("💤 {}".format(Emoji.WHITE_HEAVY_CHECK_MARK), callback_data=util.callback_for_action(
                CallbackActions.EDIT_BOT_OFFLINE, {'id': to_edit.id, 'value': False}
            )))
    else:
        buttons.append(
            InlineKeyboardButton("💤 {}".format(Emoji.HEAVY_MULTIPLICATION_X), callback_data=util.callback_for_action(
                CallbackActions.EDIT_BOT_OFFLINE, {'id': to_edit.id, 'value': True}
            )))

    buttons.append(
        InlineKeyboardButton("Delete", callback_data=util.callback_for_action(CallbackActions.CONFIRM_DELETE_BOT, bid)))

    return util.build_menu(buttons, n_cols=2)


@restricted
def edit_bot(bot, update, chat_data, bot_to_edit=None):
    chat_id = util.uid_from_update(update)
    message_id = util.mid_from_update(update)

    if not bot_to_edit:
        if update.message:
            command = update.message.text
            b_id = re.match(r'^/edit(\d+)$', command).groups()[0]

            bot_to_edit = Bot.get(id=b_id)
        else:
            util.send_message_failure(bot, chat_id, "An unexpected error occured.")
            return

    # chat_data['bot_to_edit'] = bot_to_edit

    reply_markup = InlineKeyboardMarkup(_edit_bot_buttons(bot_to_edit))
    util.send_or_edit_md_message(
        bot, chat_id,
        util.action_hint("Edit the properties of {}:{}".format(
            bot_to_edit,
            ('\n\n*Description:*\n{}'.format(bot_to_edit.description) if bot_to_edit.description else '')
        )),
        to_edit=message_id, reply_markup=reply_markup)


@restricted
def prepare_transmission(bot, update, chat_data):
    chat_id = util.uid_from_update(update)
    text = mdformat.action_hint(
        "You have the option to update the messages, or re-send the whole botlist (or not... LOL).")
    reply_markup = InlineKeyboardMarkup([[
        InlineKeyboardButton("☑ Update messages", callback_data=util.callback_for_action(
            CallbackActions.SEND_BOTLIST
        )),
        # InlineKeyboardButton("I deleted all messages. Re-Send now", callback_data=util.callback_for_action(
        #     CallbackActions.RESEND_BOTLIST
        # )),
    ]])
    util.send_md_message(bot, chat_id, text,
                         reply_markup=reply_markup)


@restricted
def approve_suggestions(bot, update):
    chat_id = util.uid_from_update(update)
    Suggestion.delete_missing()
    suggestions = Suggestion.select()[:10]

    if len(suggestions) == 0:
        util.send_or_edit_md_message(bot, chat_id, "No more suggestions available.",
                                     to_edit=util.mid_from_update(update))
        return

    buttons = []
    count = 1
    text = "Please choose suggestions to accept.\n"
    for x in suggestions:
        text += "\n{}) {}".format(count, str(x))
        buttons.append([
            InlineKeyboardButton("{}) {}".format(str(count), Emoji.WHITE_HEAVY_CHECK_MARK),
                                 callback_data=util.callback_for_action(CallbackActions.ACCEPT_SUGGESTION,
                                                                        {'id': x.id})),
            InlineKeyboardButton(Emoji.CROSS_MARK,
                                 callback_data=util.callback_for_action(CallbackActions.REJECT_SUGGESTION,
                                                                        {'id': x.id}))
        ])
        count += 1

    reply_markup = InlineKeyboardMarkup(buttons)

    util.send_or_edit_md_message(bot, chat_id, util.action_hint(text),
                                 reply_markup=reply_markup, to_edit=util.mid_from_update(update))
    return CallbackStates.APPROVING_BOTS


@restricted
def approve_bots(bot, update):
    chat_id = util.uid_from_update(update)
    unapproved = Bot.select().where(Bot.approved == False)[:10]

    if len(unapproved) == 0:
        util.send_or_edit_md_message(bot, chat_id, "No more unapproved bots available.",
                                     to_edit=util.mid_from_update(update))
        return

    unapproved_list = '\n'.join([str(x) for x in unapproved])

    buttons = []
    for x in unapproved:
        buttons.append([
            InlineKeyboardButton("{} {}".format(Emoji.WHITE_HEAVY_CHECK_MARK, x.username),
                                 callback_data=util.callback_for_action(CallbackActions.ACCEPT_BOT, {'id': x.id})),
            InlineKeyboardButton(Emoji.CROSS_MARK,
                                 callback_data=util.callback_for_action(CallbackActions.REJECT_BOT, {'id': x.id}))
        ])

    reply_markup = InlineKeyboardMarkup(buttons)
    util.send_or_edit_md_message(bot, chat_id,
                                 util.action_hint(
                                     "Please select a bot you want to accept for the BotList\n\n" + unapproved_list),
                                 reply_markup=reply_markup, to_edit=util.mid_from_update(update))
    return CallbackStates.APPROVING_BOTS


@restricted
def edit_bot_category(bot, update, for_bot, callback_action=None):
    if callback_action is None:
        callback_action = CallbackActions.EDIT_BOT_CAT_SELECTED
    chat_id = util.uid_from_update(update)
    categories = Category.select().order_by(Category.name.asc()).execute()

    buttons = util.build_menu([InlineKeyboardButton(
        '{}{}'.format(emoji.emojize(c.emojis, use_aliases=True), c.name),
        callback_data=util.callback_for_action(
            callback_action, {'cid': c.id, 'bid': for_bot.id})) for c in categories], 2)
    return util.send_or_edit_md_message(bot, chat_id, util.action_hint("Please select a category" +
                                                                       (" for {}".format(for_bot) if for_bot else '')),
                                        to_edit=util.mid_from_update(update),
                                        reply_markup=InlineKeyboardMarkup(buttons))


@restricted
def accept_bot_submission(bot, update, of_bot: Bot, category):
    chat_id = util.uid_from_update(update)
    message_id = util.mid_from_update(update)

    try:
        of_bot.category = category
        of_bot.approved = True
        of_bot.save()

        buttons = [[InlineKeyboardButton("Edit {} details".format(of_bot.username),
                                         callback_data=util.callback_for_action(CallbackActions.EDIT_BOT,
                                                                                {'id': of_bot.id}))]]
        reply_markup = InlineKeyboardMarkup(buttons)

        util.send_or_edit_md_message(bot, chat_id, "{} has been accepted to the Botlist.".format(of_bot),
                                     to_edit=message_id, reply_markup=reply_markup)
    except:
        util.send_message_failure(bot, chat_id, "An error has occured. Bot not added.")


@restricted
def send_config_files(bot, update):
    log.info("Sending config files...")
    chat_id = util.uid_from_update(update)
    bot.sendDocument(chat_id, open('files/intro_en.txt', 'rb'), filename="intro_en.txt")
    bot.sendDocument(chat_id, open('files/new_bots_list.txt', 'rb'), filename="new_bots_list.txt")
    bot.sendDocument(chat_id, open('files/category_list.txt', 'rb'), filename="category_list.txt")
    bot.sendDocument(chat_id, open('files/commands.txt', 'rb'), filename="commands.txt")


@restricted
def send_offline(bot, update):
    chat_id = util.uid_from_update(update)
    offline = Bot.select().where(Bot.offline == True)
    if len(offline) > 0:
        text = "Offline Bots:\n\n"
        text += '\n'.join(["{} — /edit{}".format(str(b), b.id) for b in offline])
    else:
        text = "No bots are offline."
    util.send_md_message(bot, chat_id, text)
