import re
from pprint import pprint

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ConversationHandler

import captions
import const
import mdformat
import settings
import util
from components import errors
from components.botlistchat import BROADCAST_REPLACEMENTS, _delete_multiple_delayed
from const import BotStates
from model import User
from util import restricted


@restricted
def pin_message(bot, update, message_id):
    cid = update.effective_chat.id
    try:
        bot.pinChatMessage(cid, message_id, False)
    except:
        errors.no_library_support(bot, update)


@restricted
def broadcast(bot, update, user_data):
    cid = update.effective_chat.id
    uid = update.effective_user.id
    mid = util.mid_from_update(update)
    user = User.from_update(update)
    text = ''

    if cid == settings.BOTLISTCHAT_ID:
        replied_to = update.message.reply_to_message
        if replied_to:
            user_data['broadcast'] = dict(user_data.get('broadcast', dict()), reply_to_message_id=replied_to.message_id)
            if replied_to.from_user.username.lower() == settings.SELF_BOT_NAME:
                # editing
                text += '*You are editing one of my messages*\n\n'
                user_data['broadcast']['mode'] = 'editing'
            else:
                # replying
                text += '*You are replying to a message of {}.*\n\n'.format(
                    update.message.reply_to_message.from_user.first_name
                )
                user_data['broadcast']['mode'] = 'replying'
        # answer and clean
        msg = bot.send_message(cid, "k")
        _delete_multiple_delayed(bot, cid, delayed=[msg.message_id], immediately=[update.message.message_id])

    to_text = "  _to_  "
    text += "Send me the text to broadcast to @BotListChat.\n"
    text += "_You can use the following words and they will replaced:_\n\n"

    text += '\n'.join(['"{}"{}{}'.format(k, to_text, v) for k, v in BROADCAST_REPLACEMENTS.items()])

    # TODO Build text mentioning replacements
    # text += '\n@' + str(update.effective_user.username) + to_text + user.markdown_short

    bot.formatter.send_or_edit(uid, mdformat.action_hint(text), mid)
    return BotStates.BROADCASTING


@restricted
def broadcast_preview(bot, update, user_data):
    uid = update.effective_user.id

    formatted_text = update.message.text_markdown
    for k, v in BROADCAST_REPLACEMENTS.items():
        # replace all occurences but mind escaping with \
        pattern = re.compile(r"(?<!\\){}".format(k), re.IGNORECASE)
        formatted_text = pattern.sub(v, formatted_text)
        formatted_text = re.sub(r"\\({})".format(k), r"\1", formatted_text, re.IGNORECASE)

    user_data['broadcast'] = dict(user_data.get('broadcast', dict()),
                                  **dict(text=formatted_text, target_chat_id=settings.BOTLISTCHAT_ID))
    mode = user_data['broadcast'].get('mode', 'just_send')

    buttons = [
        InlineKeyboardButton("Type again", callback_data=util.callback_for_action('broadcast')),
        InlineKeyboardButton("📝 Edit my message" if mode == 'editing' else "▶️ Send to @BotListChat",
                             callback_data=util.callback_for_action('send_broadcast',
                                                                    {'P4l': settings.BOTLISTCHAT_ID})),
    ]

    reply_markup = InlineKeyboardMarkup(util.build_menu(buttons, 1))
    util.send_md_message(bot, uid, formatted_text, reply_markup=reply_markup)
    return ConversationHandler.END


@restricted
def send_broadcast(bot, update, user_data):
    uid = update.effective_user.id

    try:
        bc = user_data['broadcast']
        text = bc['text']
        recipient = bc['target_chat_id']
        mode = bc.get('mode', 'just_send')
    except AttributeError:
        bot.formatter.send_failure(uid, "Missing attributes for broadcast. Aborting...")
        return ConversationHandler.END

    mid = bc.get('reply_to_message_id')

    if mode == 'replying':
        msg = util.send_md_message(bot, recipient, text, reply_to_message_id=mid)
    elif mode == 'editing':
        msg = bot.formatter.send_or_edit(recipient, text, to_edit=mid)
    else:
        msg = util.send_md_message(bot, recipient, text)

    # Post actions
    buttons = [
        InlineKeyboardButton(captions.PIN,
                             callback_data=util.callback_for_action('pin_message', {'mid': msg.message_id})),
        InlineKeyboardButton('Add "Thank You" counter',
                             callback_data=util.callback_for_action('add_thank_you',
                                                                    {'cid': recipient, 'mid': msg.message_id})),
    ]
    reply_markup = InlineKeyboardMarkup(util.build_menu(buttons, 1))
    mid = util.mid_from_update(update)
    action_taken = "edited" if mode == 'editing' else "broadcasted"
    bot.formatter.send_or_edit(uid, mdformat.success("Message {}.".format(action_taken)), mid, reply_markup=reply_markup)
