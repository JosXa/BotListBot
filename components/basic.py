import sys

import logging
import os
import signal
import time

import appglobals
import captions
import const
import mdformat
import settings
import util
from actions import Actions, MessageLinkModel, SearchQueryModel, CallbackActionModel, CategoryModel
from components import help
from components.search import search_handler, search_query
from dialog import messages
from models import Category, User
from models.statistic import Statistic, track_activity
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, \
    ReplyKeyboardRemove, Update
from telegram.error import BadRequest
from telegram.ext import CommandHandler, ConversationHandler, Filters, MessageHandler, \
    RegexHandler, ActionHandler, CallbackContext, ActionButton, RerouteToAction
from util import track_groups

log = logging.getLogger(__name__)


@track_activity('command', 'start')
@track_groups
def start(update: Update, context: CallbackContext):
    tg_user = update.message.from_user
    chat_id = tg_user.id

    # Get or create the user from/in database
    User.from_telegram_object(tg_user)

    if isinstance(context.args, list) and len(context.args) > 0:
        # CATEGORY BY ID
        try:
            cat = Category.get(Category.id == context.args[0])
            return RerouteToAction(Actions.SEND_CATEGORY, CategoryModel(cat))
        except (ValueError, Category.DoesNotExist):
            pass

        query = ' '.join(context.args).lower()

        # SPECIFIC DEEP-LINKED QUERIES
        if query == const.DeepLinkingActions.CONTRIBUTING:
            return help.contributing(context.bot, update, quote=False)
        elif query == const.DeepLinkingActions.EXAMPLES:
            return help.examples(context.bot, update, quote=False)
        elif query == const.DeepLinkingActions.RULES:
            return help.rules(context.bot, update, quote=False)
        elif query == const.DeepLinkingActions.SEARCH:
            return search_handler(context.bot, update, context.chat_data)

        # SEARCH QUERY
        return RerouteToAction(Actions.SEARCH, SearchQueryModel(query))

    else:
        context.bot.send_sticker(
            chat_id,
            open(
                os.path.join(appglobals.ROOT_DIR, 'assets', 'sticker', 'greetings-humanoids.webp'),
                'rb'))
        help.help(update, context)
        util.wait(update, context)
        if util.is_private_message(update):
            return RerouteToAction(Actions.SEND_MAIN_MENU)
        return ConversationHandler.END


def main_menu_buttons(admin=False):
    buttons = [
        [ActionButton(Actions.SELECT_CATEGORY),
         ActionButton(Actions.EXPLORE),
         ActionButton(Actions.SEND_FAVORITES)],
        [ActionButton(Actions.SEND_NEW_BOTS), ActionButton(Actions.SEARCH)],
        [ActionButton(Actions.HELP)],
    ]
    if admin:
        buttons.insert(1, [ActionButton(Actions.ADMIN_MENU)])
    return buttons


@track_activity('menu', 'main menu', Statistic.ANALYSIS)
def main_menu(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    is_admin = chat_id in settings.MODERATORS

    if util.is_private_message(update):
        reply_markup = ReplyKeyboardMarkup(
            main_menu_buttons(is_admin),
            resize_keyboard=True,
            one_time_keyboard=True)
    else:
        reply_markup = ReplyKeyboardRemove()

    update.effective_message.reply_text(
        mdformat.action_hint("What would you like to do?"),
        reply_markup=reply_markup)


@util.restricted
def restart(update: Update, context: CallbackContext):
    chat_id = update.effective_user.id
    os.kill(os.getpid(), signal.SIGINT)
    context.bot.formatter.send_success(chat_id, "Bot is restarting...")
    time.sleep(0.3)
    os.execl(sys.executable, sys.executable, *sys.argv)


def error(update: Update, context: CallbackContext):
    log.error(context.error)


@track_activity('remove', 'keyboard')
def remove_keyboard(update: Update, context: CallbackContext):
    update.message.reply_text("Keyboard removed.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END


def delete_botlistchat_promotions(update: Update, context: CallbackContext):
    cid = update.effective_chat.id

    if context.chat_data.get('delete_promotion_retries') >= 3:
        return

    if messages.PROMOTION_MESSAGE not in update.effective_message.text_markdown:
        return

    if update.effective_chat.id != settings.BOTLISTCHAT_ID:
        return

    sent_inlinequery = context.chat_data.get('sent_inlinequery')
    if sent_inlinequery:
        text = sent_inlinequery.text
        text = text.replace(messages.PROMOTION_MESSAGE, '')
        context.bot.edit_message_text(text, cid, sent_inlinequery)
        del context.chat_data['sent_inlinequery']
    else:
        context.chat_data['delete_promotion_retries'] += 1
        time.sleep(2)  # TODO
        context.update_queue.put(update)


def plaintext_group(update: Update, context: CallbackContext):
    # check if an inlinequery was sent to BotListChat

    # pprint(update.message.to_dict())
    if update.channel_post:
        return new_channel_post(context.bot, update)

        # if util.is_private_message(update):
        #     if len(update.message.text) > 3:
        #         search_query(bot, update, update.message.text, send_errors=False)

    # potentially longer operation
    context.chat_data['delete_promotion_retries'] = 0
    delete_botlistchat_promotions(update, context)


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


def count_thank_you(update: Update, context: CallbackContext, count=0):
    assert isinstance(count, int)
    update.effective_message.edit_reply_markup(reply_markup=thank_you_markup(count))


def add_thank_you_button(update: Update, context: CallbackContext[MessageLinkModel]):
    cid, mid = context.view_model.chat_id, context.view_model.message_id
    context.bot.edit_message_reply_markup(cid, mid, reply_markup=thank_you_markup(0))


def ping(update: Update, context: CallbackContext):
    update.effective_message.reply_text("pong")


@track_groups
def all_handler(update, context):
    if update.message and update.message.new_chat_members:
        if int(settings.SELF_BOT_ID) in [x.id for x in update.message.new_chat_members]:
            # bot was added to a group
            start(context.bot, update, context.chat_data, None)
    return ConversationHandler.END


def register(dp):
    dp.add_handler(ActionHandler(Actions.START, start))
    dp.add_handler(ActionHandler(Actions.SEND_MAIN_MENU, main_menu))
    dp.add_handler(RegexHandler(captions.EXIT, main_menu))
    dp.add_handler(CommandHandler('r', restart))
    dp.add_error_handler(error)
    dp.add_handler(
        MessageHandler(Filters.text & Filters.group, plaintext_group, pass_chat_data=True,
                       pass_update_queue=True))
    dp.add_handler(ActionHandler(Actions.REMOVE_KEYBOARD, remove_keyboard))


def delete_chosen_inline_result(update: Update, context: CallbackContext):
    try:
        update.message.delete()
    except BadRequest:
        pass
    except Exception as e:
        log.warning(f'Unhandled exception in delete_chosen_inline_result: {e}')
