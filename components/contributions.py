# -*- coding: utf-8 -*-
import datetime
import logging
import re

from peewee import fn

import mdformat
import settings
import util
from model import User, Bot, Suggestion, Country, Message
from telegram import ParseMode
from telegram.ext import ConversationHandler
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
        username = re.match(settings.REGEX_BOT_IN_TEXT, text).groups()[0]
        if username == '@' + settings.SELF_BOT_NAME:
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
        username = re.match(settings.REGEX_BOT_IN_TEXT, text).groups()[0]
        if username == '@' + settings.SELF_BOT_NAME:
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

    def already_reported():
        update.message.reply_text(mdformat.none_action("Someone already reported this, thanks anyway 😊"),
                                  reply_to_message_id=reply_to)

    try:
        offline_bot = Bot.get(fn.lower(Bot.username) ** username.lower(), Bot.approved == True)
        if offline_bot.offline:
            return already_reported()
        if offline_bot.official:
            update.message.reply_text(mdformat.none_action("Official bots usually don't go offline for a long time. "
                                                           "Just wait a couple hours and it will be back up ;)"),
                                      reply_to_message_id=reply_to)
            return

        try:
            Suggestion.get(action="offline", subject=offline_bot, executed=False)
            return already_reported()
        except Suggestion.DoesNotExist:
            suggestion = Suggestion(user=user, action="offline", value=True, date=datetime.date.today(),
                                    subject=offline_bot)
            suggestion.save()

        update.message.reply_text(util.success("Thank you! We will review your suggestion and set the bot offline."),
                                  reply_to_message_id=reply_to)
    except Bot.DoesNotExist:
        update.message.reply_text(
            util.action_hint("The bot you sent me is not in the @BotList."), reply_to_message_id=reply_to)
    return ConversationHandler.END


@track_groups
def new_bot_submission(bot, update, chat_data, args=None):
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
        username = re.match(settings.REGEX_BOT_IN_TEXT, text).groups()[0]
        if username == '@' + settings.SELF_BOT_NAME:
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

    description_reg = re.match(settings.REGEX_BOT_IN_TEXT + ' -\s?(.*)', text)
    description_notify = ''
    if description_reg:
        description = description_reg.group(2)
        new_bot.description = description
        description_notify = ' Your description was included.'

    new_bot.save()
    if util.is_private_message(update) and util.uid_from_update(update) in settings.MODERATORS:
        from components.explore import send_bot_details
        send_bot_details(bot, update, chat_data, new_bot)
    else:
        msg = update.message.reply_text(
            util.success("You submitted {} for approval.{}".format(new_bot, description_notify)),
            parse_mode=ParseMode.MARKDOWN, reply_to_message_id=reply_to)
        Message.get_or_create(msg, 'new', new_bot)
    return ConversationHandler.END
