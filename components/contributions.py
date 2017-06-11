# -*- coding: utf-8 -*-
import datetime
import time
import logging
import re

from peewee import fn

import const
import mdformat
import util
from dialog import messages
from model import User, Bot, Suggestion, Country
from telegram import InlineKeyboardButton
from telegram import InlineKeyboardMarkup
from telegram import ParseMode
from telegram.ext import ConversationHandler
from telegram.ext.dispatcher import run_async
from util import track_groups

logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.INFO)
log = logging.getLogger(__name__)


def notify_bot_spam(bot, update, args=None):
    tg_user = update.message.from_user
    user = User.from_telegram_object(tg_user)
    if util.stop_banned(update, user):
        return
    reply_to = util.original_reply_id(update)

    if args:
        text = ' '.join(args)
    else:
        text = update.message.text
        command_no_args = len(re.findall(r'^/spam\s*$', text)) > 0 or text.lower().strip() == '/spam@botlistbot'
        if command_no_args:
            update.message.reply_text(
                util.action_hint("Please use this command with an argument. For example:\n/spam @mybot"),
                reply_to_message_id=reply_to)
            return

    # `#spam` is already checked by handler
    try:
        username = re.match(const.REGEX_BOT_IN_TEXT, text).groups()[0]
        if username == '@' + const.SELF_BOT_NAME:
            log.info("Ignoring {}".format(text))
            return
    except AttributeError:
        if args:
            update.message.reply_text(util.failure("Sorry, but you didn't send me a bot `@username`."), quote=True,
                                      parse_mode=ParseMode.MARKDOWN, reply_to_message_id=reply_to)
        else:
            log.info("Ignoring {}".format(text))
            # no bot username, ignore update
            pass
        return

    try:
        spam_bot = Bot.get(fn.lower(Bot.username) ** username.lower(), Bot.approved == True)
        try:
            Suggestion.get(action="spam", subject=spam_bot)
        except Suggestion.DoesNotExist:
            suggestion = Suggestion(user=user, action="spam", date=datetime.date.today(), subject=spam_bot)
            suggestion.save()
        update.message.reply_text(util.success("Thank you! We will review your suggestion and mark the bot as spammy."),
                                  reply_to_message_id=reply_to)
    except Bot.DoesNotExist:
        update.message.reply_text(util.action_hint("The bot you sent me is not in the @BotList."),
                                  reply_to_message_id=reply_to)
    return ConversationHandler.END


def notify_bot_offline(bot, update, args=None):
    tg_user = update.message.from_user
    user = User.from_telegram_object(tg_user)
    if util.stop_banned(update, user):
        return
    reply_to = util.original_reply_id(update)

    if args:
        text = ' '.join(args)
    else:
        text = update.message.text
        command_no_args = len(re.findall(r'^/offline\s*$', text)) > 0 or text.lower().strip() == '/offline@botlistbot'
        if command_no_args:
            update.message.reply_text(
                util.action_hint("Please use this command with an argument. For example:\n/offline @mybot"),
                reply_to_message_id=reply_to)
            return

    # `#offline` is already checked by handler
    try:
        username = re.match(const.REGEX_BOT_IN_TEXT, text).groups()[0]
        if username == '@' + const.SELF_BOT_NAME:
            log.info("Ignoring {}".format(text))
            return
    except AttributeError:
        if args:
            update.message.reply_text(util.failure("Sorry, but you didn't send me a bot `@username`."), quote=True,
                                      parse_mode=ParseMode.MARKDOWN, reply_to_message_id=reply_to)
        else:
            log.info("Ignoring {}".format(text))
            # no bot username, ignore update
            pass
        return

    try:
        offline_bot = Bot.get(fn.lower(Bot.username) ** username.lower(), Bot.approved == True)
        try:
            Suggestion.get(action="offline", subject=offline_bot)
        except Suggestion.DoesNotExist:
            suggestion = Suggestion(user=user, action="offline", date=datetime.date.today(), subject=offline_bot)
            suggestion.save()

        if offline_bot.official:
            update.message.reply_text(mdformat.none_action("Official bots usually don't go offline for a long time. "
                                                           "Just wait a couple hours and it will be back up ;)"),
                                      reply_to_message_id=reply_to)
        else:
            update.message.reply_text(util.success("Thank you! We will review your suggestion and set the bot offline.",
                                                   ), reply_to_message_id=reply_to)
    except Bot.DoesNotExist:
        update.message.reply_text(
            util.action_hint("The bot you sent me is not in the @BotList."), reply_to_message_id=reply_to)
    return ConversationHandler.END


@track_groups
def new_bot_submission(bot, update, args=None):
    tg_user = update.message.from_user
    user = User.from_telegram_object(tg_user)
    if util.stop_banned(update, user):
        return
    reply_to = util.original_reply_id(update)

    if args:
        text = ' '.join(args)
    else:
        text = update.message.text
        command_no_args = len(re.findall(r'^/new\s*$', text)) > 0 or text.lower().strip() == '/new@botlistbot'
        if command_no_args:
            update.message.reply_text(util.action_hint(
                "Please use this command with an argument. For example:\n/new @mybot 🔎"),
                reply_to_message_id=reply_to)
            return

    # `#new` is already checked by handler
    try:
        username = re.match(const.REGEX_BOT_IN_TEXT, text).groups()[0]
        if username == '@' + const.SELF_BOT_NAME:
            log.info("Ignoring {}".format(text))
            return
    except AttributeError:
        if args:
            update.message.reply_text(util.failure("Sorry, but you didn't send me a bot `@username`."), quote=True,
                                      parse_mode=ParseMode.MARKDOWN, reply_to_message_id=reply_to)
        log.info("Ignoring {}".format(text))
        # no bot username, ignore update
        return

    try:
        new_bot = Bot.by_username(username)
        if new_bot.approved:
            update.message.reply_text(
                util.action_hint("Sorry fool, but {} is already in the @BotList 😉".format(new_bot.username)),
                reply_to_message_id=reply_to)
        else:
            update.message.reply_text(
                util.action_hint("{} has already been submitted. Please have patience...".format(new_bot.username)),
                reply_to_message_id=reply_to)
        return
    except Bot.DoesNotExist:
        new_bot = Bot(approved=False, username=username, submitted_by=user)

    new_bot.inlinequeries = "🔎" in text
    new_bot.official = "🔹" in text

    # find language
    languages = Country.select().execute()
    for lang in languages:
        if lang.emoji in text:
            new_bot.country = lang

    new_bot.date_added = datetime.date.today()

    description_reg = re.match(const.REGEX_BOT_IN_TEXT + ' -\s?(.*)', text)
    description_notify = ''
    if description_reg:
        description = description_reg.group(2)
        new_bot.description = description
        description_notify = ' Your description was included.'

    log.info("New bot submission by {}: {}".format(new_bot.submitted_by, new_bot.username))
    new_bot.save()
    if util.is_private_message(update) and util.uid_from_update(update) in const.MODERATORS:
        from bot import send_bot_details
        send_bot_details(bot, update, new_bot)
    else:
        update.message.reply_text(util.success("You submitted {} for approval.{}".format(new_bot, description_notify)),
                                  parse_mode=ParseMode.MARKDOWN, reply_to_message_id=reply_to)
    return ConversationHandler.END


def _submission_accepted_markup(accepted_bot, count=0):
    count_caption = '' if count == 0 else mdformat.number_as_emoji(count)
    button = InlineKeyboardButton('{} {}'.format(
        messages.rand_thank_you_slang(),
        count_caption
    ), callback_data=util.callback_for_action(
        const.CallbackActions.COUNT_THANK_YOU,
        {'id': accepted_bot.id, 'count': count + 1}
    ))
    return InlineKeyboardMarkup([[button]])


@run_async
def bot_submission_accepted(bot, update, accepted_bot):
    # Notify the group after 1 minute, giving the admin enough time to edit details.
    time.sleep(60)

    # check if the bot still exists
    accepted_bot = Bot.get(id=accepted_bot.id)

    text = "🆕 The bot submission by {} was accepted. This is his {} contribution.\n    *Welcome* {} *to the BotList!*".format(
        accepted_bot.submitted_by,
        accepted_bot.submitted_by.contributions_ordinal,
        accepted_bot.username
    )
    util.send_md_message(bot, const.BOTLISTCHAT_ID, text, reply_markup=_submission_accepted_markup(accepted_bot, 0))


def count_thank_you(bot, update, accepted_bot, count):
    cid = update.effective_chat.id
    update.effective_message.edit_reply_markup(reply_markup=_submission_accepted_markup(accepted_bot, count))
