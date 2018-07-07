import time

import captions
import settings
import util
from const import CallbackActions
from dialog.hints import HINTS
from models import track_activity
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Message, Update
from telegram.ext import CallbackContext
from telegram.ext.dispatcher import run_async


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


@track_activity('issued deletion of conversation in BotListChat')
def delete_conversation(update: Update, context: CallbackContext):
    cid = update.effective_chat.id
    uid = update.effective_user.id
    mid = update.effective_message.message_id

    deletions_pending = context.chat_data.get('deletions_pending', dict())
    deletion_context = deletions_pending.get(mid)

    if not deletion_context:
        return

    if uid != deletion_context['user_id']:
        if uid not in settings.MODERATORS:
            update.callback_query.answer(text="✋️ You didn't prompt this message.")
            return

    context.bot.delete_message(cid, mid)
    context.bot.delete_message(cid, deletion_context['command_id'])


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
def show_available_hints(update: Update, context: CallbackContext):
    message = "In @BotListChat, you can use the following hashtags to guide new members:\n\n"
    message += '\n'.join(
        '🗣 {tag} ➖ {help}'.format(
            tag=k, help=v['help']
        ) for k, v in HINTS.items()
    )
    message += "\n\nMake sure to reply to another message, so I know who to refer to."
    update.effective_message.reply_text(message, parse_mode='markdown',
                                        disable_web_page_preview=True)


def get_hint_message_and_markup(text):
    for k, v in HINTS.items():
        if k not in text:
            continue

        text = text.replace(k, '')
        query = text.strip()

        reply_markup = None
        if v.get('buttons'):
            # Replace 'query' placeholder and expand kwargs
            buttons = [InlineKeyboardButton(
                **{k: v.format(query=query) for k, v in b.items()}
            ) for b in v.get('buttons')]
            reply_markup = InlineKeyboardMarkup(util.build_menu(buttons, 1))

        msg = v['message'].format(
            query=query if query else v['default'] if v.get('default') else '')
        return msg, reply_markup, k
    return None, None, None


@run_async
def hint_handler(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    if chat_id not in [settings.BOTLISTCHAT_ID, settings.BOTLIST_NOTIFICATIONS_ID,
                       settings.BLSF_ID]:
        return
    text = update.message.text
    reply_to = update.message.reply_to_message

    msg, reply_markup, _ = get_hint_message_and_markup(text)

    if msg is not None:
        context.bot.formatter.send_message(chat_id, msg, reply_markup=reply_markup,
                                   reply_to_message_id=reply_to.message_id if reply_to else None)
        update.effective_message.disable()


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
