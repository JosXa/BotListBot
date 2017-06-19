import time
from pprint import pprint

from telegram import InlineKeyboardButton
from telegram import InlineKeyboardMarkup
from telegram import Message
from telegram.ext.dispatcher import run_async

import captions
import const
import util
from components.contributions import _submission_accepted_markup
from const import CallbackActions
from model import Bot


def append_delete_button(update, chat_data, reply_markup):
    uid = update.effective_user.id
    cid = update.effective_chat.id
    command_mid = update.effective_message.message_id
    if not isinstance(reply_markup, InlineKeyboardMarkup):
        return reply_markup, callable
    if cid != const.BOTLISTCHAT_ID:
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
            pprint(deletions_pending)

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
    print('current message id: {}'.format(mid))
    context = deletions_pending.get(mid)
    print('associated context:')
    pprint(context)

    if not context:
        return

    if uid != context['user_id']:
        if uid not in const.MODERATORS:
            bot.answerCallbackQuery(update.callback_query.id, text="✋️ You didn't prompt this message.")
            return

    bot.delete_message(cid, mid)
    bot.delete_message(cid, context['command_id'])


@run_async
def notify_group_submission_accepted(bot, job, accepted_bot):
    # check if the bot still exists
    accepted_bot = Bot.get(id=accepted_bot.id)

    text = "*Welcome* {} *to the BotList!*\n🏆 This submission by {} is " \
           "their {} contribution.".format(
        str(accepted_bot),
        str(accepted_bot.submitted_by),
        accepted_bot.submitted_by.contributions_ordinal,
    )
    util.send_md_message(bot, const.BOTLISTCHAT_ID, text, reply_markup=_submission_accepted_markup(accepted_bot, 0))
