import logging
import os
import signal
import time
from pprint import pprint

import sys

from telegram import KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardButton, \
    InlineKeyboardMarkup
from telegram.ext import CommandHandler
from telegram.ext import ConversationHandler
from telegram.ext import Filters
from telegram.ext import MessageHandler
from telegram.ext import RegexHandler

import appglobals
import captions
import const
import mdformat
import settings
import util
from components import help
from components.botlist import new_channel_post
from components.search import search_query, search_handler
from dialog import messages
from model import User, Category
from model.statistic import track_activity, Statistic
from util import track_groups

log = logging.getLogger(__name__)


@track_activity('command', 'start')
@track_groups
def start(bot, update, chat_data, args):
    tg_user = update.message.from_user
    chat_id = tg_user.id

    # Get or create the user from/in database
    User.from_telegram_object(tg_user)

    if isinstance(args, list) and len(args) > 0:
        # CATEGORY BY ID
        try:
            cat = Category.get(Category.id == args[0])
            from components.explore import send_category
            return send_category(bot, update, chat_data, cat)
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
            return search_handler(bot, update, chat_data)

        # SEARCH QUERY
        search_query(bot, update, chat_data, query)

    else:
        bot.sendSticker(chat_id,
                        open(os.path.join(appglobals.ROOT_DIR, 'assets', 'sticker', 'greetings-humanoids.webp'), 'rb'))
        help.help(bot, update)
        util.wait(bot, update)
        if util.is_private_message(update):
            main_menu(bot, update)
        return ConversationHandler.END


def main_menu_buttons(admin=False):
    buttons = [
        [KeyboardButton(captions.CATEGORIES), KeyboardButton(captions.EXPLORE), KeyboardButton(captions.FAVORITES)],
        [KeyboardButton(captions.NEW_BOTS), KeyboardButton(captions.SEARCH)],
        [KeyboardButton(captions.HELP)],
    ]
    if admin:
        buttons.insert(1, [KeyboardButton(captions.ADMIN_MENU)])
    return buttons


@track_activity('menu', 'main menu', Statistic.ANALYSIS)
def main_menu(bot, update):
    chat_id = update.effective_chat.id
    is_admin = chat_id in settings.MODERATORS
    reply_markup = ReplyKeyboardMarkup(main_menu_buttons(is_admin),
                                       resize_keyboard=True, one_time_keyboard=True) if util.is_private_message(
        update) else ReplyKeyboardRemove()

    bot.sendMessage(chat_id, mdformat.action_hint("What would you like to do?"),
                    reply_markup=reply_markup)


@util.restricted
def restart(bot, update):
    chat_id = util.uid_from_update(update)
    os.kill(os.getpid(), signal.SIGINT)
    bot.formatter.send_success(chat_id, "Bot is restarting...")
    time.sleep(0.3)
    os.execl(sys.executable, sys.executable, *sys.argv)


def error(bot, update, error):
    log.error(error)


@track_activity('remove', 'keyboard')
def remove_keyboard(bot, update):
    update.message.reply_text("Keyboard removed.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END


def delete_botlistchat_promotions(bot, update, chat_data, update_queue):
    cid = update.effective_chat.id

    if chat_data.get('delete_promotion_retries') >= 3:
        return

    if messages.PROMOTION_MESSAGE not in update.effective_message.text_markdown:
        return

    if update.effective_chat.id != settings.BOTLISTCHAT_ID:
        return

    sent_inlinequery = chat_data.get('sent_inlinequery')
    if sent_inlinequery:
        text = sent_inlinequery.text
        text = text.replace(messages.PROMOTION_MESSAGE, '')
        bot.edit_message_text(text, cid, sent_inlinequery)
        del chat_data['sent_inlinequery']
    else:
        chat_data['delete_promotion_retries'] += 1
        time.sleep(2)  # TODO
        update_queue.put(update)


def plaintext_group(bot, update, chat_data, update_queue):
    # check if an inlinequery was sent to BotListChat

    # pprint(update.message.to_dict())
    if update.channel_post:
        return new_channel_post(bot, update)

        # if util.is_private_message(update):
        #     if len(update.message.text) > 3:
        #         search_query(bot, update, update.message.text, send_errors=False)

    # potentially longer operation
    chat_data['delete_promotion_retries'] = 0
    delete_botlistchat_promotions(bot, update, chat_data, update_queue)


def cancel(bot, update):
    return ConversationHandler.END


def thank_you_markup(count=0):
    assert isinstance(count, int)
    count_caption = '' if count == 0 else mdformat.number_as_emoji(count)
    button = InlineKeyboardButton('{} {}'.format(
        messages.rand_thank_you_slang(),
        count_caption
    ), callback_data=util.callback_for_action(
        const.CallbackActions.COUNT_THANK_YOU,
        {'count': count + 1}
    ))
    return InlineKeyboardMarkup([[button]])


def count_thank_you(bot, update, count=0):
    assert isinstance(count, int)
    update.effective_message.edit_reply_markup(reply_markup=thank_you_markup(count))


def add_thank_you_button(bot, update, cid, mid):
    bot.edit_message_reply_markup(cid, mid, reply_markup=thank_you_markup(0))


@track_groups
def all_handler(bot, update, chat_data):
    if update.message and update.message.new_chat_members:
        if int(settings.SELF_BOT_ID) in [x.id for x in update.message.new_chat_members]:
            # bot was added to a group
            start(bot, update, chat_data, None)
    return ConversationHandler.END


def register(dp):
    dp.add_handler(CommandHandler('start', start, pass_args=True, pass_chat_data=True))
    dp.add_handler(CommandHandler("menu", main_menu))
    dp.add_handler(RegexHandler(captions.EXIT, main_menu))
    dp.add_handler(CommandHandler('r', restart))
    dp.add_error_handler(error)
    dp.add_handler(
        MessageHandler(Filters.text & Filters.group, plaintext_group, pass_chat_data=True, pass_update_queue=True))
    dp.add_handler(CommandHandler("removekeyboard", remove_keyboard))
