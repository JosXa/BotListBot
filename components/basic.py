import os
import sys
import time

import captions
import const
import mdformat
import util
from bot import send_category, search_handler, search_query, log
from components import help
from components.botlist import new_channel_post
from model import User, Category
from telegram import KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import CommandHandler
from telegram.ext import ConversationHandler
from telegram.ext import Filters
from telegram.ext import MessageHandler
from telegram.ext import RegexHandler
from util import track_groups, restricted


@track_groups
def start(bot, update, args):
    tg_user = update.message.from_user
    chat_id = tg_user.id

    # Get or create the user from/in database
    User.from_telegram_object(tg_user)

    if len(args) > 0:
        # CATEGORY BY ID
        try:
            cat = Category.get(Category.id == args[0])
            return send_category(bot, update, cat)
        except (ValueError, Category.DoesNotExist):
            pass

        query = ' '.join(args).lower()

        # SPECIFIC DEEP-LINKED QUERIES
        if query == const.DeepLinkingActions.CONTRIBUTING:
            return help.contributing(bot, update, quote=False)
        elif query == const.DeepLinkingActions.EXAMPLES:
            return help.examples(bot, update, quote=False)
        elif query == const.DeepLinkingActions.RULES:
            return help.rules(bot, update, quote=False)
        elif query == const.DeepLinkingActions.SEARCH:
            return search_handler(bot, update)

        # SEARCH QUERY
        search_query(bot, update, query)

    else:
        help.help(bot, update)
        util.wait(bot, update)
        if util.is_private_message(update):
            main_menu(bot, update)
        return ConversationHandler.END


def _main_menu_buttons(admin=False):
    buttons = [
        [KeyboardButton(captions.CATEGORIES), KeyboardButton(captions.FAVORITES)],
        [KeyboardButton(captions.NEW_BOTS), KeyboardButton(captions.SEARCH)],
        [KeyboardButton(captions.HELP)],
    ]
    if admin:
        buttons.insert(1, [KeyboardButton(captions.ADMIN_MENU)])
    return buttons


def main_menu(bot, update):
    chat_id = update.effective_chat.id
    is_admin = chat_id in const.MODERATORS
    reply_markup = ReplyKeyboardMarkup(_main_menu_buttons(is_admin),
                                       resize_keyboard=True) if util.is_private_message(
        update) else ReplyKeyboardRemove()

    bot.sendMessage(chat_id, mdformat.action_hint("What would you like to do?"),
                    reply_markup=reply_markup)


@restricted
def restart(bot, update):
    chat_id = util.uid_from_update(update)
    # if not admin.check_admin(chat_id):
    #     return
    util.send_message_success(bot, chat_id, "Bot is restarting...")
    time.sleep(0.2)
    os.execl(sys.executable, sys.executable, *sys.argv)


def error(bot, update, error):
    log.error(error)


def remove_keyboard(bot, update):
    update.message.reply_text("Keyboard removed.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END


@track_groups
def plaintext(bot, update):
    # pprint(update.message.to_dict())
    if update.channel_post:
        return new_channel_post(bot, update)

        # if util.is_private_message(update):
        #     if len(update.message.text) > 3:
        #         search_query(bot, update, update.message.text, send_errors=False)


def cancel(bot, update):
    return ConversationHandler.END


def register(dp):
    dp.add_handler(CommandHandler('start', start, pass_args=True))
    dp.add_handler(CommandHandler("menu", main_menu))
    dp.add_handler(RegexHandler(captions.EXIT, main_menu))
    dp.add_handler(CommandHandler('r', restart))
    dp.add_error_handler(error)
    dp.add_handler(MessageHandler(Filters.text & Filters.group, plaintext, edited_updates=True))
    dp.add_handler(CommandHandler("removekeyboard", remove_keyboard))
