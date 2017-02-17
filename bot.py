# -*- coding: utf-8 -*-
import datetime
import json
import logging
import os
import re
import sys
import time
from pprint import pprint
from uuid import uuid4

import emoji
from peewee import fn
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram import InlineQueryResultArticle
from telegram import InputTextMessageContent
from telegram import ParseMode
from telegram.ext import CallbackQueryHandler
from telegram.ext import MessageHandler, \
    Filters, RegexHandler, InlineQueryHandler, ConversationHandler
from telegram.ext import Updater, CommandHandler

import appglobals
import captions
import components.botlist
import const
import util
from components import admin
from components import botlist
from components import botproperties
from components.admin import edit_bot_category
from components.botlist import new_channel_post
from const import BotStates, CallbackActions, CallbackStates
from model import Category, Bot, Country, Channel
from model.suggestion import Suggestion
from model.user import User
from util import restricted, private_chat_only

logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.INFO)
log = logging.getLogger(__name__)

"""
TODO:
- make regexes case-insensitive
- TEST - delete suggestions where bot does not exist anymore
- add /credits for people who have a lot of bot submissions
- if inline query yields no category result, try to find a BOT **like that query and send the corresponding category
"""


def start(bot, update, args):
    tg_user = update.message.from_user
    chat_id = tg_user.id

    # Get or create the user from/in database
    user = User.from_telegram_object(tg_user)

    if len(args) > 0:
        # 1st arg: category id
        try:
            cat = Category.get(Category.id == args[0])
            return select_bot_from_category(bot, update, cat)
        except Category.DoesNotExist:
            util.send_message_failure(bot, chat_id, "The requested category does not exist.")
        return
    help(bot, update)


@restricted
def restart(bot, update):
    chat_id = util.uid_from_update(update)
    # if not admin.check_admin(chat_id):
    #     return
    util.send_message_success(bot, chat_id, "Bot is restarting...")
    time.sleep(0.2)
    os.execl(sys.executable, sys.executable, *sys.argv)


def select_category(bot, update, callback_action=None):
    if callback_action is None:
        # set default
        callback_action = CallbackActions.SELECT_BOT_FROM_CATEGORY
    chat_id = util.uid_from_update(update)
    categories = Category.select().order_by(Category.name.asc()).execute()

    buttons = util.build_menu([InlineKeyboardButton(
        '{}{}'.format(emoji.emojize(c.emojis, use_aliases=True), c.name),
        callback_data=util.callback_for_action(
            callback_action, {'id': c.id})) for c in categories], 2)
    msg = util.send_or_edit_md_message(bot, chat_id, util.action_hint("Please select a category"),
                                       to_edit=util.mid_from_update(update),
                                       reply_markup=InlineKeyboardMarkup(buttons))
    # return msg


def inlinequery(bot, update):
    query = update.inline_query.query
    chat_id = update.inline_query.from_user.id
    results_list = list()
    categories = list()

    try:
        # user selected a specific category
        c = Category.get((Category.name ** query) | (Category.extra ** query))
        categories.append(c)
    except Category.DoesNotExist:
        # no search results, send all
        categories = Category.select()

    for c in categories:
        bot_list = Bot.select().where(Bot.category == c, Bot.approved == True)
        bots_with_description = [b for b in bot_list if b.description is not None]

        txt = const.PROMOTION_MESSAGE + '\n\n'
        txt += "There are *{}* bots in the category *{}*:\n\n".format(len(bot_list), str(c))
        txt += '\n'.join([str(b) for b in bot_list])
        results_list.append(InlineQueryResultArticle(
            id=uuid4(),
            title=emoji.emojize(c.emojis, use_aliases=True) + c.name,
            input_message_content=InputTextMessageContent(message_text=txt, parse_mode="Markdown"),
            description=c.extra
        ))

    bot.answerInlineQuery(update.inline_query.id, results=results_list)


def error(bot, update, error):
    log.error(error)


def help(bot, update):
    update.message.reply_text(const.HELP_MESSAGE, quote=True, parse_mode=ParseMode.MARKDOWN)
    update.message.reply_text('*Available commands:*\n' + const.COMMANDS, parse_mode=ParseMode.MARKDOWN)


def contributing(bot, update):
    update.message.reply_text(const.CONTRIBUTING_MESSAGE, quote=True, parse_mode=ParseMode.MARKDOWN)


def examples(bot, update):
    chat_id = util.uid_from_update(update)
    update.message.reply_text(const.EXAMPLES_MESSAGE, quote=True, parse_mode=ParseMode.MARKDOWN)


def rules(bot, update):
    pass


def credits(bot, update):
    # TODO: test
    Bot.select(Bot.submitted_by)


def photo_handler(bot, update):
    if update.channel_post:
        pic = update.message.photo
        return new_channel_post(bot, update, pic)


def plaintext(bot, update):
    if update.channel_post:
        return new_channel_post(bot, update)

        # print("Plaintext received: {}".format(update.message.text))


def notify_bot_offline(bot, update, args=None):
    tg_user = update.message.from_user
    user = User.from_telegram_object(tg_user)
    if args:
        text = ' '.join(args)
    else:
        text = update.message.text
        command_no_args = len(re.findall(r'^/new\s*$', text)) > 0
        if command_no_args:
            update.message.reply_text(
                util.action_hint("Please use this command with an argument. For example:\n\n/offline @mybot"))
            return

    # `#offline` is already checked by handler
    try:
        username = re.match(const.REGEX_BOT_IN_TEXT, text).groups()[0]
    except AttributeError:
        if args:
            update.message.reply_text(util.failure("Sorry, but you didn't send me a bot `@username`."), quote=True,
                                      parse_mode=ParseMode.MARKDOWN)
        else:
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
        update.message.reply_text(util.success("Thank you! We will review your suggestion and set the bot offline."))
    except Bot.DoesNotExist:
        update.message.reply_text(util.action_hint("The bot you sent me is not in the @botlist."))


def new_bot_submission(bot, update, args=None):
    tg_user = update.message.from_user
    user = User.from_telegram_object(tg_user)
    if args:
        text = ' '.join(args)
    else:
        text = update.message.text
        command_no_args = len(re.findall(r'^/new\s*$', text)) > 0
        if command_no_args:
            update.message.reply_text(util.action_hint(
                "Please use this command with an argument. For example:\n\n/new @mybot 🔎"))
            return

    # `#new` is already checked by handler
    try:
        username = re.match(const.REGEX_BOT_IN_TEXT, text).groups()[0]
    except AttributeError:
        if args:
            update.message.reply_text(util.failure("Sorry, but you didn't send me a bot `@username`."), quote=True,
                                      parse_mode=ParseMode.MARKDOWN)
        # no bot username, ignore update
        return

    languages = Country.select().execute()
    try:
        new_bot = Bot.by_username(username)
        if new_bot.approved:
            update.message.reply_text(
                util.action_hint("Sorry fool, but {} is already in the @botlist 😉".format(new_bot.username)))
        else:
            update.message.reply_text(
                util.action_hint("{} has already been submitted. Please have patience...".format(new_bot.username)))
        return
    except Bot.DoesNotExist:
        new_bot = Bot(approved=False, username=username, submitted_by=user)

    new_bot.inlinequeries = "🔎" in text
    new_bot.official = "🔹" in text

    # find language
    for lang in languages:
        if lang.emoji in text:
            new_bot.country = lang

    new_bot.date_added = datetime.date.today()

    # TODO: allow users to suggest a category
    # new_bot.category = cat

    log.info("New bot submission by {}: {}".format(new_bot.submitted_by, new_bot.username))
    new_bot.save()
    update.message.reply_text(util.success("You submitted {} for approval.".format(new_bot)),
                              parse_mode=ParseMode.MARKDOWN)


def select_bot_from_category(bot, update, category=None):
    chat_id = util.uid_from_update(update)
    bot_list = Bot.select().where(Bot.category == category, Bot.approved == True)
    bots_with_description = [b for b in bot_list if b.description is not None]

    callback = CallbackActions.SEND_BOT_DETAILS

    buttons = [InlineKeyboardButton(x.username, callback_data=util.callback_for_action(
        callback, {'id': x.id})) for x in bots_with_description]
    menu = util.build_menu(buttons, 2)
    menu.insert(0, [
        InlineKeyboardButton(captions.BACK, callback_data=util.callback_for_action(
            CallbackActions.SELECT_CATEGORY
        )),
        InlineKeyboardButton("Share", switch_inline_query=category.name)
    ])
    txt = "There are *{}* bots in the category *{}*:\n\n".format(len(bot_list), str(category))

    if chat_id in const.ADMINS:
        # append edit buttons
        txt += '\n'.join(["{} — /edit{}".format(b, b.id) for b in bot_list])
    else:
        txt += '\n'.join([str(b) for b in bot_list])

    if len(bots_with_description) > 0:
        txt += "\n\n" + util.action_hint("Press a button below to get a detailed description.")
    util.send_or_edit_md_message(bot, chat_id,
                                 txt,
                                 to_edit=util.mid_from_update(update), reply_markup=InlineKeyboardMarkup(menu))


@private_chat_only
def send_bot_details(bot, update, item=None):
    chat_id = util.uid_from_update(update)

    if item is None:
        try:
            text = update.message.text
            bot_in_text = re.findall(const.REGEX_BOT_IN_TEXT, text)[0]
            item = Bot.by_username(bot_in_text)

            if item.description is None:
                # make reply_markup if user is admin and talking to the bot in private
                reply_markup = None
                # private_message = (update.message and update.message.chat.type == 'private')
                if chat_id in const.ADMINS:
                    reply_markup = InlineKeyboardMarkup([[
                        InlineKeyboardButton("Edit {}".format(item.username),
                                             callback_data=util.callback_for_action(
                                                 CallbackActions.EDIT_BOT,
                                                 {'id': item.id}
                                             ))
                    ]])
                update.message.reply_text(util.success(
                    "{} is in the @{}."
                        # \n\nIt has no description yet."" \
                        .format(item.username,
                                const.SELF_CHANNEL_USERNAME)),
                    reply_markup=reply_markup)
                return
        # except (AttributeError, Bot.DoesNotExist):
        except (Bot.DoesNotExist):
            update.message.reply_text(util.failure("This bot is not in the @{}.".format(const.SELF_CHANNEL_USERNAME)))
            return

    reply_markup = InlineKeyboardMarkup([[
        InlineKeyboardButton(captions.BACK, callback_data=util.callback_for_action(
            CallbackActions.SELECT_BOT_FROM_CATEGORY, {'id': item.category.id}
        ))
    ]])
    util.send_or_edit_md_message(bot, chat_id,
                                 "*{}*\n\n"
                                 "{}\n\n".format(item, item.description),
                                 to_edit=util.mid_from_update(update),
                                 reply_markup=reply_markup
                                 )
    return CallbackStates.SHOWING_BOT_DETAILS


# def category_permalink(bot, update, category):
#     import urllib.parse
#     link = "http://telegram.me/{}/{}".format(urllib.parse.quote_plus(const.SELF_CHANNEL_USERNAME), category.current_message_id)
#     link = "http://google.com"
#     bot.answerCallbackQuery(update.callback_query.id, url=link)


def callback_router(bot, update, chat_data):
    obj = json.loads(str(update.callback_query.data))
    if 'a' in obj:
        action = obj['a']

        # BASIC QUERYING
        if action == CallbackActions.SELECT_CATEGORY:
            select_category(bot, update)
        if action == CallbackActions.SELECT_BOT_FROM_CATEGORY:
            category = Category.get(id=obj['id'])
            select_bot_from_category(bot, update, category)
        if action == CallbackActions.SEND_BOT_DETAILS:
            item = Bot.get(id=obj['id'])
            send_bot_details(bot, update, item)
        # if action == CallbackActions.PERMALINK:
        #     category = Category.get(id=obj['cid'])
        #     category_permalink(bot, update, category)
        # SEND BOTLIST
        if action == CallbackActions.SEND_BOTLIST:
            components.botlist.send_botlist(bot, update, chat_data)
        if action == CallbackActions.RESEND_BOTLIST:
            components.botlist.send_botlist(bot, update, chat_data, resend=True)
        # ACCEPT/REJECT BOT SUBMISSIONS
        if action == CallbackActions.ACCEPT_BOT:
            to_accept = Bot.get(id=obj['id'])
            edit_bot_category(bot, update, to_accept, CallbackActions.BOT_ACCEPTED)
        if action == CallbackActions.REJECT_BOT:
            to_reject = Bot.get(id=obj['id'])
            to_reject.delete_instance()
            admin.approve_bots(bot, update)
        if action == CallbackActions.BOT_ACCEPTED:
            to_accept = Bot.get(id=obj['bid'])
            category = Category.get(id=obj['cid'])
            admin.accept_bot_submission(bot, update, to_accept, category)
        # ADD BOT
        if action == CallbackActions.ADD_BOT_SELECT_CAT:
            category = Category.get(id=obj['id'])
            admin.add_bot(bot, update, chat_data, category)
        # EDIT BOT
        if action == CallbackActions.EDIT_BOT:
            to_edit = Bot.get(id=obj['id'])
            admin.edit_bot(bot, update, chat_data, to_edit)
        if action == CallbackActions.EDIT_BOT_SELECT_CAT:
            to_edit = Bot.get(id=obj['id'])
            edit_bot_category(bot, update, to_edit)
        if action == CallbackActions.EDIT_BOT_CAT_SELECTED:
            to_edit = Bot.get(id=obj['bid'])
            to_edit.category = Category.get(id=obj['cid'])
            to_edit.save()
            admin.edit_bot(bot, update, chat_data, to_edit)
        if action == CallbackActions.EDIT_BOT_COUNTRY:
            to_edit = Bot.get(id=obj['id'])
            botproperties.set_country(bot, update, to_edit)
        if action == CallbackActions.SET_COUNTRY:
            to_edit = Bot.get(id=obj['bid'])
            if obj['cid'] == 'None':
                country = None
            else:
                country = Country.get(id=obj['cid'])
            to_edit.country = country
            to_edit.save()
            admin.edit_bot(bot, update, chat_data, to_edit)
        if action == CallbackActions.EDIT_BOT_DESCRIPTION:
            to_edit = Bot.get(id=obj['id'])
            return botproperties.set_description(bot, update, chat_data, to_edit)
        if action == CallbackActions.EDIT_BOT_EXTRA:
            to_edit = Bot.get(id=obj['id'])
            return botproperties.set_extra(bot, update, chat_data, to_edit)
        if action == CallbackActions.EDIT_BOT_NAME:
            to_edit = Bot.get(id=obj['id'])
            return botproperties.set_name(bot, update, chat_data, to_edit)
        if action == CallbackActions.EDIT_BOT_USERNAME:
            to_edit = Bot.get(id=obj['id'])
            return botproperties.set_username(bot, update, chat_data, to_edit)
        if action == CallbackActions.EDIT_BOT_INLINEQUERIES:
            to_edit = Bot.get(id=obj['id'])
            botproperties.toggle_inlinequeries(bot, update, to_edit)
            admin.edit_bot(bot, update, chat_data, to_edit)
        if action == CallbackActions.EDIT_BOT_OFFICIAL:
            to_edit = Bot.get(id=obj['id'])
            botproperties.toggle_official(bot, update, to_edit)
            admin.edit_bot(bot, update, chat_data, to_edit)
        if action == CallbackActions.EDIT_BOT_OFFLINE:
            to_edit = Bot.get(id=obj['id'])
            botproperties.toggle_offline(bot, update, to_edit)
            admin.edit_bot(bot, update, chat_data, to_edit)
        if action == CallbackActions.CONFIRM_DELETE_BOT:
            to_delete = Bot.get(id=obj['id'])
            botproperties.delete_bot_confirm(bot, update, to_delete)
        if action == CallbackActions.DELETE_BOT:
            to_edit = Bot.get(id=obj['id'])
            botproperties.delete_bot(bot, update, to_edit)
            select_bot_from_category(bot, update, to_edit.category)
        if action == CallbackActions.ACCEPT_SUGGESTION:
            suggestion = Suggestion.get(id=obj['id'])
            botproperties.accept_suggestion(bot, update, suggestion)
            admin.approve_suggestions(bot, update)
        if action == CallbackActions.REJECT_SUGGESTION:
            suggestion = Suggestion.get(id=obj['id'])
            suggestion.delete_instance()
            admin.approve_suggestions(bot, update)


def main():
    try:
        BOT_TOKEN = str(os.environ['TG_TOKEN'])
    except Exception:
        # BOT_TOKEN = str(sys.argv[1])
        BOT_TOKEN = "265482650:AAEABaV06JMB3k5QnyWvbP4-_3S-wyxLG4M"  # live
        # BOT_TOKEN = "182355371:AAGYq_ZfFss6foI51jb753gvB3skk6RAV84"  # dev
    try:
        PORT = str(os.environ['PORT'])
    except Exception:
        PORT = None
    try:
        URL = str(os.environ['URL'])
    except Exception:
        URL = None

    updater = Updater(BOT_TOKEN, workers=2)

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    conv_handler = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(callback_router, pass_chat_data=True),
            CommandHandler('category', select_category),
            CommandHandler('cat', select_category),
            # CallbackQueryHandler(callback_router, pass_chat_data=True)
        ],
        states={
            BotStates.SENDING_DESCRIPTION: [
                MessageHandler(Filters.text, botproperties.set_description, pass_chat_data=True)
            ],
            BotStates.SENDING_EXTRA: [
                MessageHandler(Filters.text, botproperties.set_extra, pass_chat_data=True)
            ],
            BotStates.SENDING_NAME: [
                MessageHandler(Filters.text, botproperties.set_name, pass_chat_data=True)
            ],
            BotStates.SENDING_USERNAME: [
                MessageHandler(Filters.text, botproperties.set_username, pass_chat_data=True)
            ],
        },
        fallbacks=[
            CallbackQueryHandler(callback_router, pass_chat_data=True),
            CommandHandler('cat', select_category),
            CommandHandler('start', start, pass_args=True),
        ]
    )
    conv_handler.allow_reentry = True
    dp.add_handler(conv_handler)

    dp.add_handler(CommandHandler('start', start, pass_args=True))
    dp.add_handler(CommandHandler("admin", admin.menu))
    dp.add_handler(CommandHandler("promo", botlist.preview_promo_message))
    dp.add_handler(RegexHandler(captions.APPROVE_BOTS + '.*', admin.approve_bots))
    dp.add_handler(RegexHandler(captions.APPROVE_SUGGESTIONS + '.*', admin.approve_suggestions))
    dp.add_handler(RegexHandler(captions.SEND_BOTLIST, admin.prepare_transmission, pass_chat_data=True))
    dp.add_handler(RegexHandler(captions.SEND_CONFIG_FILES, admin.send_config_files))
    dp.add_handler(RegexHandler(captions.FIND_OFFLINE, admin.send_offline))

    dp.add_handler(RegexHandler("^/edit\d+$", admin.edit_bot, pass_chat_data=True))
    dp.add_handler(CommandHandler('new', new_bot_submission, pass_args=True))
    dp.add_handler(RegexHandler('.*#new.*', new_bot_submission))
    dp.add_handler(CommandHandler('offline', notify_bot_offline, pass_args=True))
    dp.add_handler(RegexHandler('.*#offline.*', notify_bot_offline))
    dp.add_handler(RegexHandler('^{}$'.format(const.REGEX_BOT_ONLY), send_bot_details))

    dp.add_handler(CommandHandler('r', restart))
    dp.add_handler(CommandHandler('help', help))
    dp.add_handler(CommandHandler("contributing", contributing))
    dp.add_handler(CommandHandler("examples", examples))
    dp.add_handler(InlineQueryHandler(inlinequery))
    dp.add_error_handler(error)
    dp.add_handler(MessageHandler(Filters.text, plaintext))
    dp.add_handler(MessageHandler(Filters.photo, photo_handler))

    # if PORT and URL:
    #     updater.start_webhook(listen='0.0.0.0', port=PORT, url_path=BOT_TOKEN)
    #     updater.bot.setWebhook(URL +
    #                            BOT_TOKEN)
    # else:
    updater.start_polling()

    log.info('Listening...')
    updater.idle()
    log.info('Disconnecting...')
    appglobals.disconnect()


if __name__ == '__main__':
    main()
