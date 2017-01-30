# -*- coding: utf-8 -*-
import datetime
import json
import logging
import os
import re
import sys
import time
from itertools import chain
from pprint import pprint
from uuid import uuid4

import emoji
from telegram import InlineQueryResultArticle
from telegram import InputTextMessageContent
from telegram import ParseMode
from telegram import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from telegram import Update
from telegram.ext import MessageHandler, \
    Filters, RegexHandler, InlineQueryHandler, ConversationHandler
from telegram.ext import Updater, CommandHandler

import captions
import const
import helpers
import util
from components import admin
from const import BotStates, CallbackActions, CallbackStates
from jsoncallbackhandler import JSONCallbackHandler
from model import Category, Bot, Country, Channel
from model.user import User
from util import restricted

logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.INFO)
log = logging.getLogger(__name__)


def start(bot, update, args):
    print("/start")
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
    chat_id = util.cid_from_update(update)
    # if not admin.check_admin(chat_id):
    #     return
    util.send_message_success(bot, chat_id, "Bot is restarting...")
    time.sleep(0.2)
    os.execl(sys.executable, sys.executable, *sys.argv)


def select_category(bot, update, callback_action=CallbackActions.CATEGORY_SELECTED):
    chat_id = util.cid_from_update(update)
    categories = Category.select().order_by(Category.name.asc()).execute()

    buttons = util.build_menu([InlineKeyboardButton(
        '{}{}'.format(emoji.emojize(c.emojis, use_aliases=True), c.name),
        callback_data=util.callback_for_action(
            callback_action, {'id': c.id})) for c in categories], 2)
    util.send_or_edit_md_message(bot, chat_id, util.action_hint("Please select a category"),
                                 to_edit=util.mid_from_update(update),
                                 reply_markup=InlineKeyboardMarkup(buttons))
    return CallbackStates.SELECTING_CATEGORY


def edit_bot_category(bot, update, for_bot, callback_action=CallbackActions.EDIT_BOT_CAT_SELECTED):
    chat_id = util.cid_from_update(update)
    categories = Category.select().order_by(Category.name.asc()).execute()

    buttons = util.build_menu([InlineKeyboardButton(
        '{}{}'.format(emoji.emojize(c.emojis, use_aliases=True), c.name),
        callback_data=util.callback_for_action(
            callback_action, {'cid': c.id, 'bid': for_bot.id})) for c in categories], 2)
    return util.send_or_edit_md_message(bot, chat_id, util.action_hint("Please select a category" +
                                                                       (" for {}".format(for_bot) if for_bot else '')),
                                        to_edit=util.mid_from_update(update),
                                        reply_markup=InlineKeyboardMarkup(buttons))


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
        print(str(c))
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
    chat_id = util.cid_from_update(update)
    util.send_md_message(bot, chat_id, "*The BotListBot is currently in development*. You can use it, but please do not complain about bugs for the time being. Be patient, and thank you!")
    update.message.reply_text(const.HELP_MESSAGE, parse_mode=ParseMode.MARKDOWN)
    update.message.reply_text('Available commands:\n' + helpers.get_commands(), parse_mode=ParseMode.MARKDOWN)


def new_channel_post(bot, update, photo=None):
    post = update.channel_post
    pprint(update.channel_post.to_dict())
    text = post.text

    channel, created = Channel.get_or_create(chat_id=post.chat_id, username=post.chat.username)
    channel.last_message_id = post.message_id
    channel.save()
    print("Updated last_message_id to {}.".format(channel.last_message_id))

    category_list = '•Share your bots to the @BotListChat using the hashtag #new' in text
    intro = 'Hi! Welcome' in text
    category = text[0] == '•' and not category_list
    new_bots_list = 'NEW→' in text

    # TODO: is this a document?
    if photo:
        pass
    elif category:
        try:
            # get the category meta data
            meta = re.match(r'•(.*?)([A-Z].*):(?:\n(.*):)?', text).groups()
            if len(meta) < 2:
                raise ValueError("Category could not get parsed.")

            emojis = str.strip(meta[0])
            name = str.strip(meta[1])
            extra = str.strip(meta[2]) if meta[2] else None
            try:
                cat = Category.get(name=name)
            except Category.DoesNotExist:
                cat = Category(name=name)
            cat.emojis = emojis
            cat.extra = extra
            cat.save()

            # get the bots in that category
            bots = re.findall(r'^(@\w+)( \W+)?$', text, re.MULTILINE)
            languages = Country.select().execute()
            for b in bots:
                username = b[0]
                try:
                    new_bot = Bot.get(username=username)
                except Bot.DoesNotExist:
                    new_bot = Bot(username=username)

                new_bot.inlinequeries = "🔎" in b[1]
                new_bot.official = "🔹" in b[1]

                # find language
                for lang in languages:
                    if lang.emoji in b[1]:
                        new_bot.country = lang

                new_bot.date_added = datetime.date.today()
                new_bot.category = cat

                new_bot.save()
        except AttributeError:
            log.error("Error parsing the following text:\n" + text)
            # elif intro:
            #     with codecs.open('files/intro.txt', 'w', 'utf-8') as f:
            #         f.write(text)
            # elif category_list:
            #     with codecs.open('files/category_list.txt', 'w', 'utf-8') as f:
            #         f.write(text)
            # elif new_bots_list:
            #     with codecs.open('files/new_bots_list.txt', 'w', 'utf-8') as f:
            #         f.write(text)


def photo_handler(bot, update):
    if update.channel_post:
        pic = update.message.photo
        return new_channel_post(bot, update, pic)


def plaintext(bot, update):
    print("Plaintext received: {}".format(update.message.text))
    if update.channel_post:
        return new_channel_post(bot, update)


def new_bot_submission(bot, update: Update):
    text = update.message.text
    user = update.message.from_user

    # `#new` is already checked by handler
    try:
        username = re.match(r'.*(@[a-zA-Z0-9_\-]*).*', text).groups()[0]
    except AttributeError:
        # no bot username, ignore update
        return

    languages = Country.select().execute()
    try:
        new_bot = Bot.get(username=username)
        update.message.reply_text(
            util.action_hint("{} was already submitted. Please have patience...".format(username)))
        return
    except Bot.DoesNotExist:
        new_bot = Bot(approved=False, username=username, submitted_by=user.to_json())

    new_bot.inlinequeries = "🔎" in text
    new_bot.official = "🔹" in text

    # find language
    for lang in languages:
        if lang.emoji in text:
            new_bot.country = lang

    new_bot.date_added = datetime.date.today()

    # TODO: allow users to suggest a category
    # new_bot.category = cat

    new_bot.save()
    update.message.reply_text(util.success("You submitted {} for approval.".format(new_bot)))


def select_bot_from_category(bot, update, category=None):
    chat_id = util.cid_from_update(update)
    bot_list = Bot.select().where(Bot.category == category, Bot.approved == True)
    bots_with_description = [b for b in bot_list if b.description is not None]

    callback = CallbackActions.SEND_BOT_DETAILS

    buttons = [InlineKeyboardButton(x.username, callback_data=util.callback_for_action(
        callback, {'id': x.id})) for x in bots_with_description]
    menu = util.build_menu(buttons, 2)
    menu.insert(0, [
        InlineKeyboardButton(captions.BACK, callback_data=util.callback_for_action(
            CallbackActions.BACK, {'id': category.id}
        )),
        InlineKeyboardButton("Share", switch_inline_query=category.name)
    ])
    txt = "There are *{}* bots in the category *{}*:\n\n".format(len(bot_list), str(category))
    txt += '\n'.join([str(b) for b in bot_list])
    if len(bots_with_description) > 0:
        txt += "\n\n" + util.action_hint("Press a button below to get a detailed description.")
    util.send_or_edit_md_message(bot, chat_id,
                                 txt,
                                 to_edit=util.mid_from_update(update), reply_markup=InlineKeyboardMarkup(menu))
    return CallbackStates.SELECTING_BOT


def send_bot_details(bot, update, item: Bot):
    chat_id = util.cid_from_update(update)
    reply_markup = InlineKeyboardMarkup([[
        InlineKeyboardButton(captions.BACK, callback_data=util.callback_for_action(
            CallbackActions.BACK, {'id': item.category.id}
        ))
    ]])
    util.send_or_edit_md_message(bot, chat_id,
                                 "*{}*\n\n"
                                 "{}\n\n".format(item, item.description),
                                 to_edit=util.mid_from_update(update),
                                 reply_markup=reply_markup
                                 )
    return CallbackStates.SHOWING_BOT_DETAILS


def callback_router(bot, update, chat_data):
    print("WTF!!!")
    obj = json.loads(str(update.callback_query.data))
    if 'a' in obj:
        action = obj['a']

        if action == CallbackActions.SELECT_BOT_IN_CATEGORY:
            category = Category.get(id=obj['id'])
            select_bot_from_category(bot, update, category)
        if action == CallbackActions.SEND_BOT_DETAILS:
            item = Bot.get(id=obj['id'])
            send_bot_details(bot, update, item)
        if action == CallbackActions.ADD_BOT_SELECT_CAT:
            category = Category.get(id=obj['id'])
            admin.add_bot(bot, update, chat_data, category)
        if action == CallbackActions.EDIT_BOT_SELECT_CAT:
            select_category(bot, update, CallbackActions.EDIT_BOT_CAT_SELECTED)
        if action == CallbackActions.SELECT_CATEGORY:
            select_category(bot, update)
        if action == CallbackActions.EDIT_BOT_CAT_SELECTED:
            category = Category.get(id=obj['id'])
            select_bot_from_category(bot, update, category, CallbackActions.EDIT_BOT_SELECT_BOT)
        if action == CallbackActions.EDIT_BOT_SELECT_BOT:
            bot = Bot.get(id=obj['id'])
            admin.edit_bot(bot, update, chat_data, bot_to_edit=bot)
        if action == CallbackActions.SEND_BOTLIST:
            admin.send_botlist(bot, update, chat_data)
        if action == CallbackActions.RESEND_BOTLIST:
            admin.send_botlist(bot, update, chat_data, resend=True)
        if action == CallbackActions.ACCEPT_BOT:
            to_accept = Bot.get(id=obj['id'])
            edit_bot_category(bot, update, to_accept, CallbackActions.ACCEPT_BOT_CAT_SELECTED)
        if action == CallbackActions.ACCEPT_BOT_CAT_SELECTED:
            to_accept = Bot.get(id=obj['id'])
            edit_bot_category(bot, update, to_accept, CallbackActions.ACCEPT_BOT_CAT_SELECTED)


def main():
    try:
        BOT_TOKEN = str(os.environ['TG_TOKEN'])
    except Exception:
        # BOT_TOKEN = str(sys.argv[1])
        BOT_TOKEN = "265482650:AAEABaV06JMB3k5QnyWvbP4-_3S-wyxLG4M"
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

    # some also in callback_query_handler
    admin_menu = [
        RegexHandler(captions.ADD_BOT, admin.add_bot, pass_chat_data=True),
        RegexHandler(captions.APPROVE_BOTS + '.*', admin.approve_bots),
        RegexHandler(captions.EDIT_BOT, admin.edit_bot, pass_chat_data=True),
        RegexHandler(captions.SEND_BOTLIST, admin.prepare_transmission, pass_chat_data=True),
    ]

    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("admin", admin.menu),
            CommandHandler('category', select_category),
            CommandHandler('start', start, pass_args=True),
            JSONCallbackHandler(CallbackActions.SELECT_CATEGORY, select_category)
            # CallbackQueryHandler(callback_router, pass_chat_data=True)
        ],
        states={
            BotStates.ADMIN_MENU: admin_menu,
            BotStates.ADMIN_ADDING_BOT: chain(
                admin_menu,
                [MessageHandler(Filters.text, admin.add_bot, pass_chat_data=True)]
            ),
            CallbackStates.SELECTING_CATEGORY: [
                JSONCallbackHandler(CallbackActions.CATEGORY_SELECTED, select_bot_from_category,
                                    mapping={'id': (Category, 'category')})
            ],
            CallbackStates.SELECTING_BOT: [
                JSONCallbackHandler(CallbackActions.BACK, select_category),
                JSONCallbackHandler(CallbackActions.SEND_BOT_DETAILS, send_bot_details,
                                    mapping={'id': (Bot, 'item')})
            ],
            CallbackStates.SHOWING_BOT_DETAILS: [
                JSONCallbackHandler(CallbackActions.BACK, select_bot_from_category,
                                    mapping={'id': (Category, 'category')})
            ],
            CallbackStates.APPROVING_BOTS: [
                JSONCallbackHandler(CallbackActions.ACCEPT_BOT, admin.accept_bot,
                                    mapping={'id': (Bot, 'item')}, pass_chat_data=True)
            ]
        },
        fallbacks=chain(admin_menu, [
        ])

    )
    conv_handler.allow_reentry = True
    dp.add_handler(conv_handler)



    # dp.add_handler(CommandHandler('start', select_bot_from_category))
    # TODO: #new-emoji
    dp.add_handler(RegexHandler('.*#new.*', new_bot_submission))
    dp.add_handler(CommandHandler('r', restart))
    dp.add_handler(CommandHandler('help', help))
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


if __name__ == '__main__':
    main()
