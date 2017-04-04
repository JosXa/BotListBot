# -*- coding: utf-8 -*-
import logging
import re
from pprint import pprint

import datetime
import emoji
from telegram.ext import ConversationHandler, Job

import helpers
from model import User
from telegram import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup, TelegramError

import captions
import const
import mdformat
import messages
import util
from const import *
from const import BotStates, CallbackActions
from custemoji import Emoji
from model import Bot
from model import Category
from model import Keyword
from model import Suggestion
from util import restricted

logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.INFO)
log = logging.getLogger(__name__)


@restricted
def menu(bot, update):
    uid = util.uid_from_update(update)

    buttons = _admin_buttons(uid in const.ADMINS)

    util.send_md_message(bot, uid, "🛃 Administration menu",
                         reply_markup=ReplyKeyboardMarkup(buttons, resize_keyboard=True))
    return BotStates.ADMIN_MENU


def _admin_buttons(send_botlist_button=True):
    n_unapproved = len(Bot.select().where(Bot.approved == False))
    n_suggestions = len(Suggestion.select_all())

    second_row = list()
    if n_unapproved > 0:
        second_row.append(KeyboardButton(captions.APPROVE_BOTS + ' ({} 🆕)'.format(n_unapproved)))
    if n_suggestions > 0:
        second_row.append(KeyboardButton(captions.APPROVE_SUGGESTIONS + ' ({})'.format(n_suggestions)))

    buttons = [[
        KeyboardButton(captions.EXIT)
    ], [
        KeyboardButton(captions.FIND_OFFLINE),
        KeyboardButton(captions.SEND_CONFIG_FILES)
    ]]

    if send_botlist_button:
        buttons.insert(1, [KeyboardButton(captions.SEND_BOTLIST)])

    if len(second_row) > 0:
        buttons.insert(1, second_row)

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
        InlineKeyboardButton("Set keywords",
                             callback_data=util.callback_for_action(
                                 CallbackActions.EDIT_BOT_KEYWORDS, bid
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

    # offline
    if to_edit.spam:
        buttons.append(
            InlineKeyboardButton("🚮 {}".format(Emoji.WHITE_HEAVY_CHECK_MARK), callback_data=util.callback_for_action(
                CallbackActions.EDIT_BOT_SPAM, {'id': to_edit.id, 'value': False}
            )))
    else:
        buttons.append(
            InlineKeyboardButton("🚮 {}".format(Emoji.HEAVY_MULTIPLICATION_X), callback_data=util.callback_for_action(
                CallbackActions.EDIT_BOT_SPAM, {'id': to_edit.id, 'value': True}
            )))

    buttons.append(
        InlineKeyboardButton("Delete", callback_data=util.callback_for_action(CallbackActions.CONFIRM_DELETE_BOT, bid)))

    header = [InlineKeyboardButton(captions.BACK,
                                   callback_data=util.callback_for_action(CallbackActions.SELECT_BOT_FROM_CATEGORY,
                                                                          {'id': to_edit.category.id}))]

    return util.build_menu(buttons, n_cols=2, header_buttons=header)


@restricted
def edit_bot(bot, update, chat_data, bot_to_edit=None):
    chat_id = util.uid_from_update(update)
    message_id = util.mid_from_update(update)
    kws = Keyword.select().where(Keyword.entity == bot_to_edit)

    if not bot_to_edit:
        if update.message:
            command = update.message.text
            b_id = re.match(r'^/edit(\d+)$', command).groups()[0]

            try:
                bot_to_edit = Bot.get(id=b_id)
            except Bot.DoesNotExist:
                update.message.reply_text(util.failure('No bot exists with this id.'))
                return
        else:
            util.send_message_failure(bot, chat_id, "An unexpected error occured.")
            return

    # chat_data['bot_to_edit'] = bot_to_edit

    reply_markup = InlineKeyboardMarkup(_edit_bot_buttons(bot_to_edit))
    util.send_or_edit_md_message(
        bot, chat_id,
        "🛃 Edit {}".format(bot_to_edit.detail_text),
        to_edit=message_id, reply_markup=reply_markup)
    return


@restricted
def prepare_transmission(bot, update, chat_data):
    chat_id = util.uid_from_update(update)
    text = mdformat.action_hint(
        "Notify subscribers about this update?")
    reply_markup = InlineKeyboardMarkup([[
        InlineKeyboardButton("☑ Notifications (delete footer)", callback_data=util.callback_for_action(
            CallbackActions.SEND_BOTLIST, {'silent': False}
        )),
        InlineKeyboardButton("Silent update", callback_data=util.callback_for_action(
            CallbackActions.SEND_BOTLIST, {'silent': True}
        ))], [
        InlineKeyboardButton("Re-send all Messages (delete first)", callback_data=util.callback_for_action(
            CallbackActions.SEND_BOTLIST, {'silent': True, 're': True}))
    ]])
    util.send_md_message(bot, chat_id, text,
                         reply_markup=reply_markup)


@restricted
def approve_suggestions(bot, update, page=0):
    chat_id = util.uid_from_update(update)
    suggestions = Suggestion.select_all()
    if page * const.PAGE_SIZE_SUGGESTIONS_LIST >= len(suggestions):
        # old item deleted, list now too small
        page = page - 1 if page > 0 else 0
    start = page * const.PAGE_SIZE_SUGGESTIONS_LIST
    end = start + const.PAGE_SIZE_SUGGESTIONS_LIST

    has_prev_page = page > 0
    has_next_page = page * const.PAGE_SIZE_SUGGESTIONS_LIST < len(suggestions)
    suggestions = suggestions[start:end]

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
                                                                        {'id': x.id, 'page': page})),
            InlineKeyboardButton(Emoji.CROSS_MARK,
                                 callback_data=util.callback_for_action(CallbackActions.REJECT_SUGGESTION,
                                                                        {'id': x.id, 'page': page}))
        ])
        count += 1
    page_arrows = list()
    if has_prev_page:
        page_arrows.append(InlineKeyboardButton(Emoji.LEFTWARDS_BLACK_ARROW,
                                                callback_data=util.callback_for_action(
                                                    CallbackActions.SWITCH_SUGGESTIONS_PAGE,
                                                    {'page': page - 1})))
    if has_next_page:
        page_arrows.append(InlineKeyboardButton(Emoji.BLACK_RIGHTWARDS_ARROW,
                                                callback_data=util.callback_for_action(
                                                    CallbackActions.SWITCH_SUGGESTIONS_PAGE,
                                                    {'page': page + 1})))
    buttons.append(page_arrows)

    reply_markup = InlineKeyboardMarkup(buttons)

    util.send_or_edit_md_message(bot, chat_id, util.action_hint(text),
                                 reply_markup=reply_markup, to_edit=util.mid_from_update(update))
    return CallbackStates.APPROVING_BOTS


@restricted
def approve_bots(bot, update, page=0):
    chat_id = util.uid_from_update(update)
    unapproved = Bot.select().where(Bot.approved == False).order_by(Bot.date_added)
    if page * const.PAGE_SIZE_APPROVALS_LIST >= len(unapproved):
        # old item deleted, list now too small
        page = page - 1 if page > 0 else 0
    start = page * const.PAGE_SIZE_APPROVALS_LIST
    end = start + const.PAGE_SIZE_APPROVALS_LIST
    has_prev_page = page > 0
    has_next_page = (page + 1) * const.PAGE_SIZE_APPROVALS_LIST < len(unapproved)
    unapproved = unapproved[start:end]

    if len(unapproved) == 0:
        util.send_or_edit_md_message(bot, chat_id, "No more unapproved bots available.",
                                     to_edit=util.mid_from_update(update))
        return

    buttons = []
    for x in unapproved:
        buttons.append([
            InlineKeyboardButton(Emoji.WHITE_HEAVY_CHECK_MARK,
                                 callback_data=util.callback_for_action(CallbackActions.ACCEPT_BOT, {'id': x.id})),
            InlineKeyboardButton(x.username, url="http://t.me/{}".format(x.username[1:])),
            InlineKeyboardButton(Emoji.CROSS_MARK,
                                 callback_data=util.callback_for_action(CallbackActions.REJECT_BOT,
                                                                        {'id': x.id, 'page': page, 'ntfc': True})),
            InlineKeyboardButton('🗑',
                                 callback_data=util.callback_for_action(CallbackActions.REJECT_BOT,
                                                                        {'id': x.id, 'page': page, 'ntfc': False}))
        ])
    page_arrows = list()
    if has_prev_page:
        page_arrows.append(InlineKeyboardButton(Emoji.LEFTWARDS_BLACK_ARROW,
                                                callback_data=util.callback_for_action(
                                                    CallbackActions.SWITCH_APPROVALS_PAGE,
                                                    {'page': page - 1})))
    if has_next_page:
        page_arrows.append(InlineKeyboardButton(Emoji.BLACK_RIGHTWARDS_ARROW,
                                                callback_data=util.callback_for_action(
                                                    CallbackActions.SWITCH_APPROVALS_PAGE,
                                                    {'page': page + 1})))
    buttons.append(page_arrows)

    reply_markup = InlineKeyboardMarkup(buttons)
    util.send_or_edit_md_message(bot, chat_id,
                                 util.action_hint(
                                     "Please select a bot you want to accept for the BotList"),
                                 reply_markup=reply_markup, to_edit=util.mid_from_update(update))
    return CallbackStates.APPROVING_BOTS


@restricted
def edit_bot_category(bot, update, for_bot, callback_action=None):
    if callback_action is None:
        callback_action = CallbackActions.EDIT_BOT_CAT_SELECTED
    uid = util.uid_from_update(update)
    categories = Category.select().order_by(Category.name.asc()).execute()

    buttons = util.build_menu([InlineKeyboardButton(
        '{}{}'.format(emoji.emojize(c.emojis, use_aliases=True), c.name),
        callback_data=util.callback_for_action(
            callback_action, {'cid': c.id, 'bid': for_bot.id})) for c in categories], 2)
    return util.send_or_edit_md_message(bot, uid, util.action_hint("Please select a category" +
                                                                   (" for {}".format(for_bot) if for_bot else '')),
                                        to_edit=util.mid_from_update(update),
                                        reply_markup=InlineKeyboardMarkup(buttons))


@restricted
def accept_bot_submission(bot, update, of_bot: Bot, category):
    chat_id = util.uid_from_update(update)
    message_id = util.mid_from_update(update)

    try:
        of_bot.category = category
        of_bot.date_added = datetime.date.today()
        of_bot.approved = True
        of_bot.save()

        buttons = [[InlineKeyboardButton("Edit {} details".format(of_bot.username),
                                         callback_data=util.callback_for_action(CallbackActions.EDIT_BOT,
                                                                                {'id': of_bot.id}))]]
        reply_markup = InlineKeyboardMarkup(buttons)

        util.send_or_edit_md_message(bot, chat_id, "{} has been accepted to the Botlist.".format(of_bot),
                                     to_edit=message_id, reply_markup=reply_markup)

        log_msg = "{} accepted by {}.".format(of_bot.username, chat_id)
        # notify submittant
        try:
            bot.sendMessage(of_bot.submitted_by.chat_id,
                            util.success(messages.ACCEPTANCE_PRIVATE_MESSAGE.format(of_bot.username)))
            log_msg += "\nUser {} was notified.".format(str(of_bot.submitted_by))
        except TelegramError:
            log_msg += "\nUser {} could NOT be contacted/notified in private.".format(str(of_bot.submitted_by))
        log.info(log_msg)
    except:
        util.send_message_failure(bot, chat_id, "An error has occured. Bot not added.")


@restricted
def send_config_files(bot, update):
    log.info("Sending config files...")
    chat_id = util.uid_from_update(update)
    bot.sendDocument(chat_id, open('files/intro_en.txt', 'rb'), filename="intro_en.txt")
    bot.sendDocument(chat_id, open('files/intro_es.txt', 'rb'), filename="intro_es.txt")
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


@restricted
def reject_bot_submission(bot, update, to_reject=None, verbose=True, notify_submittant=True):
    uid = util.uid_from_update(update)

    if to_reject is None:
        if not update.message.reply_to_message:
            update.message.reply_text(util.failure("You must reply to a message of mine."))
            return
        text = update.message.reply_to_message.text

        try:
            username = re.match(const.REGEX_BOT_IN_TEXT, text).groups()[0]
        except AttributeError:
            log.info("No username in the message that was replied to.")
            # no bot username, ignore update
            return

        try:
            to_reject = Bot.by_username(username)
        except Bot.DoesNotExist:
            log.info("Rejection failed: could not find {}".format(username))
            return

        if to_reject.approved is True:
            bot.sendMessage(uid, util.failure(
                "{} has already been accepted, so it cannot be rejected anymore.".format(username)))
            return

    log_msg = "{} rejected by {}.".format(to_reject.username, uid)
    if notify_submittant:
        try:
            bot.sendMessage(to_reject.submitted_by.chat_id,
                            util.failure(messages.REJECTION_PRIVATE_MESSAGE.format(to_reject.username)))
            log_msg += "\nUser {} was notified.".format(str(to_reject.submitted_by))
        except TelegramError:
            log_msg += "\nUser {} could NOT be contacted/notified in private.".format(str(to_reject.submitted_by))
    to_reject.delete_instance()
    log.info(log_msg)
    if verbose:
        bot.sendMessage(uid, util.success("{} rejected.".format(to_reject.username)))


def last_update_job(bot, job: Job):
    ## SEND A MESSAGE
    # user_ids = [u.chat_id for u in User.select()]
    # not_sent = list()
    # for uid in user_ids:
    #     import bot as botlistbot
    #     try:
    #         bot.sendMessage(uid, "Hey, check out my new Keyboard! 😍",
    #                         reply_markup=ReplyKeyboardMarkup(botlistbot._main_menu_buttons()))
    #     except TelegramError:
    #         not_sent.append(uid)
    # pprint(not_sent)

    last_update = helpers.get_channel().last_update
    if last_update:
        today = datetime.date.today()
        delta = datetime.timedelta(days=const.BOT_CONSIDERED_NEW)
        difference = today - last_update

        if difference > delta:
            for a in const.MODERATORS:
                try:
                    bot.sendMessage(a, "Last @BotList update was {} days ago. UPDATE NOW YOU CARNT! /admin".format(
                        difference.days))
                except TelegramError:
                    pass
