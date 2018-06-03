# -*- coding: utf-8 -*-
import datetime
import re
from logzero import logger as log
from peewee import fn
from pprint import pprint
from pyrogram.api.errors import UsernameNotOccupied
from telegram import Message as TelegramMessage, ParseMode
from telegram.ext import ConversationHandler, run_async

import settings
import util
from appglobals import loop
from components.admin import notify_submittant_rejected
from components.userbot import BotChecker
from components.userbot.botchecker import add_keywords, download_profile_picture
from model import Bot, Country, Suggestion, User
from model.revision import Revision
from util import track_groups


def extract_bot_mentions(message: TelegramMessage):
    text = message.text

    matches = re.findall(settings.REGEX_BOT_IN_TEXT, text)
    pprint(matches)

    # If it ends in "bot", we can be sure it's a bot.
    # Other ones will be thrown away, assuming that we already have all the verified bots


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
        command_no_args = len(
            re.findall(r'^/spam\s*$', text)) > 0 or text.lower().strip() == '/spam@botlistbot'
        if command_no_args:
            update.message.reply_text(
                util.action_hint(
                    "Please use this command with an argument. For example:\n/spam @mybot"),
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
            update.message.reply_text(
                util.failure("Sorry, but you didn't send me a bot `@username`."), quote=True,
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
            suggestion = Suggestion(user=user, action="spam", date=datetime.date.today(),
                                    subject=spam_bot)
            suggestion.save()
        update.message.reply_text(
            util.success("Thank you! We will review your suggestion and mark the bot as spammy."),
            reply_to_message_id=reply_to)
    except Bot.DoesNotExist:
        update.message.reply_text(util.action_hint("The bot you sent me is not in the @BotList."),
                                  reply_to_message_id=reply_to)
    return ConversationHandler.END


def notify_bot_offline(bot, update, args=None):
    tg_user = update.message.from_user
    update.message.reply_text(
        "Thanks, but the BotList now automatically detects when a bot goes offline 😇😍")
    return


@track_groups
def new_bot_submission(bot, update, chat_data, args=None, bot_checker=None):
    tg_user = update.message.from_user
    user = User.from_telegram_object(tg_user)
    if util.stop_banned(update, user):
        return
    reply_to = util.original_reply_id(update)

    if args:
        text = ' '.join(args)
    else:
        text = update.message.text
        command_no_args = len(
            re.findall(r'^/new\s*$', text)) > 0 or text.lower().strip() == '/new@botlistbot'
        if command_no_args:
            update.message.reply_text(util.action_hint(
                "Please use this command with an argument. For example:\n/new @mybot 🔎"),
                reply_to_message_id=reply_to)
            return

    # `#new` is already checked by handler
    try:
        username = re.match(settings.REGEX_BOT_IN_TEXT, text).groups()[0]
        if username.lower() == '@' + settings.SELF_BOT_NAME.lower():
            log.info("Ignoring {}".format(text))
            return
    except AttributeError:
        if args:
            update.message.reply_text(
                util.failure("Sorry, but you didn't send me a bot `@username`."), quote=True,
                parse_mode=ParseMode.MARKDOWN, reply_to_message_id=reply_to)
        log.info("Ignoring {}".format(text))
        # no bot username, ignore update
        return

    try:
        new_bot = Bot.by_username(username, include_disabled=True)
        if new_bot.disabled:
            update.message.reply_text(
                util.failure(
                    "{} is banned from the @BotList.".format(new_bot.username)),
                reply_to_message_id=reply_to)
        elif new_bot.approved:
            update.message.reply_text(
                util.action_hint(
                    "Sorry fool, but {} is already in the @BotList 😉".format(new_bot.username)),
                reply_to_message_id=reply_to)
        else:
            update.message.reply_text(
                util.action_hint("{} has already been submitted. Please have patience...".format(
                    new_bot.username)),
                reply_to_message_id=reply_to)
        return
    except Bot.DoesNotExist:
        new_bot = Bot(revision=Revision.get_instance().next, approved=False, username=username,
                      submitted_by=user)

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

    check_submission(bot, bot_checker, new_bot)

    return ConversationHandler.END


@run_async
def check_submission(bot, bot_checker: BotChecker, to_check: Bot):
    # TODO: make this method async
    if bot_checker is None:
        return

    botlistbot_user = User.botlist_user_instance()

    log.debug("Checking bot {}...".format(to_check.username))

    def reject(reason):
        to_check.delete_instance()
        msg = notify_submittant_rejected(
            bot,
            botlistbot_user,
            notify_submittant=True,
            reason=reason,
            to_reject=to_check
        )
        bot.formatter.send_message(settings.BOTLIST_NOTIFICATIONS_ID, msg)

    try:
        peer = bot_checker.resolve_bot(to_check)
    except UsernameNotOccupied:
        to_check.delete_instance()
        reject("The entity you submitted either does not exist or is not a Telegram bot.")
        return

    bot_checker.update_bot_details(to_check, peer)

    if to_check.userbot:
        reject("You submitted the name of a Telegram user, not one of a bot. If you're trying to "
               "submit a userbot, please contact the BLSF directly ("
               "@BotListChat).")
        return

    # Check online state
    response = loop.run_until_complete(
        bot_checker.get_ping_response(
            to_check,
            timeout=18,
            try_inline=to_check.inlinequeries
        )
    )

    is_offline = not bool(response)

    if is_offline:
        reject("The bot you sent seems to be offline, unfortunately. Feel free to submit it again "
               "when it's back up 😙")
        return

    now = datetime.datetime.now()
    to_check.last_ping = now
    to_check.last_response = now

    loop.run_until_complete(add_keywords(bot, response, to_check))

    # Download profile picture
    if settings.DOWNLOAD_PROFILE_PICTURES:
        # TODO: does this work asynchronously?
        loop.run_until_complete(download_profile_picture(bot, bot_checker, to_check))

    to_check.save()
    log.info(f"{to_check} was evaluated and looks good for approval.")

    # if settings.DELETE_CONVERSATION_AFTER_PING:
    #     await bot_checker.schedule_conversation_deletion(to_check.chat_id, 10)
