import logging
import time

from telegram import InlineKeyboardButton
from telegram import InlineKeyboardMarkup
from telegram import Message
from telegram.ext.dispatcher import run_async

import captions
import const
import settings
import util
from components import basic
from const import CallbackActions
from model import Bot

logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.INFO)
log = logging.getLogger(__name__)


def append_delete_button(update, chat_data, reply_markup):
    uid = update.effective_user.id
    cid = update.effective_chat.id
    command_mid = update.effective_message.message_id
    if not isinstance(reply_markup, InlineKeyboardMarkup):
        return reply_markup, callable
    if cid != settings.BOTLISTCHAT_ID:
        return reply_markup, callable

    def append_callback(message):
        if message is None:
            return
        if isinstance(message, Message):
            mid = message.message_id
        else:
            mid = message
        deletions_pending = chat_data.get('deletions_pending', dict())
        if not deletions_pending.get(mid):
            deletions_pending[mid] = dict(user_id=uid, command_id=command_mid)
            chat_data['deletions_pending'] = deletions_pending

    buttons = reply_markup.inline_keyboard
    buttons.append([
        InlineKeyboardButton(captions.random_done_delete(), callback_data=util.callback_for_action(
            CallbackActions.DELETE_CONVERSATION))
    ])
    reply_markup.inline_keyboard = buttons
    return reply_markup, append_callback


def delete_conversation(bot, update, chat_data):
    cid = update.effective_chat.id
    uid = update.effective_user.id
    mid = util.mid_from_update(update)

    deletions_pending = chat_data.get('deletions_pending', dict())
    context = deletions_pending.get(mid)

    if not context:
        return

    if uid != context['user_id']:
        if uid not in settings.MODERATORS:
            bot.answerCallbackQuery(update.callback_query.id, text="✋️ You didn't prompt this message.")
            return

    bot.delete_message(cid, mid)
    bot.delete_message(cid, context['command_id'])


BROADCAST_REPLACEMENTS = {
    'categories': '📚 ᴄᴀᴛɢᴏʀɪᴇs',
    'bots': '🤖 *bots*',
    '- ': '👉 '
}


@run_async
def _delete_multiple_delayed(bot, chat_id, immediately=None, delayed=None):
    if immediately is None:
        immediately = []
    if delayed is None:
        delayed = []

    for mid in immediately:
        bot.delete_message(chat_id, mid)

    time.sleep(1.5)

    for mid in delayed:
        bot.delete_message(chat_id, mid)


@run_async
def notify_group_submission_accepted(bot, job, accepted_bot):
    # accepted_bot = Bot.get(id=accepted_bot.id)
    # log.info("Notifying group about new accepted bot {}".format(accepted_bot.username))
    # # check if the bot still exists
    #
    # text = "*Welcome* {} *to the BotList!*\n🏆 This submission by {} is " \
    #        "their {} contribution.".format(
    #     str(accepted_bot),
    #     str(accepted_bot.submitted_by),
    #     accepted_bot.submitted_by.contributions_ordinal,
    # )
    # util.send_md_message(bot, settings.BOTLISTCHAT_ID, text,
    #                      reply_markup=basic.thank_you_markup(0), disable_web_page_preview=True)

    pass  # upon @T3CHNO's request :((((


def text_message_logger(bot, update, logger):
    pass
    # cid = update.effective_chat.id
    # if cid != settings.BOTLISTCHAT_ID:
    #     return
    # text = "{}: {}".format(update.effective_user.first_name, update.message.text)
    # logger.info(text)
