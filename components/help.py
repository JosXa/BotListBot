import captions
import const
import helpers
import settings
import util
from actions import Actions
from dialog import messages
from helpers import reroute_private_chat
from telegram import InlineKeyboardButton, Update
from telegram import InlineKeyboardMarkup
from telegram import ParseMode
from telegram.ext import ConversationHandler, CallbackContext, ActionButton

from models import track_activity
from util import track_groups


def available_commands(bot, update):
    update.message.reply_text('*Available commands:*\n' + helpers.get_commands(), parse_mode=ParseMode.MARKDOWN)


@track_groups
@track_activity('command', 'help')
def help(update: Update, context: CallbackContext):
    mid = update.effective_message.message_id
    cid = update.effective_chat.id
    context.bot.formatter.send_or_edit(cid, messages.HELP_MESSAGE_ENGLISH, to_edit=mid, reply_markup=_help_markup())
    return ConversationHandler.END


@track_activity('command', 'contributing')
def contributing(update: Update, context: CallbackContext):
    mid = update.effective_message.message_id
    cid = update.effective_chat.id
    context.bot.formatter.send_or_edit(cid, messages.CONTRIBUTING, to_edit=mid, reply_markup=_help_markup())
    return ConversationHandler.END


@track_activity('command', 'examples')
def examples(update: Update, context: CallbackContext):
    mid = update.effective_message.message_id
    cid = update.effective_chat.id
    context.bot.formatter.send_or_edit(cid, messages.EXAMPLES, to_edit=mid, reply_markup=_help_markup())
    return ConversationHandler.END


@track_activity('command', 'rules')
def rules(update: Update, context: CallbackContext, quote=True):
    chat_id = update.effective_chat.id
    if chat_id == settings.BOTLISTCHAT_ID or util.is_private_message(update):
        reroute_private_chat(context.bot, update, quote, const.DeepLinkingActions.RULES, messages.BOTLISTCHAT_RULES)
    else:
        update.message.reply_text("Sorry, but I don't know the rules in this group 👻\n\n" + messages.PROMOTION_MESSAGE,
                                  parse_mode=ParseMode.MARKDOWN)
    return ConversationHandler.END


def _help_markup():
    buttons = [[
        ActionButton(Actions.HELP),
        ActionButton(Actions.CONTRIBUTING),
        ActionButton(Actions.EXAMPLES),
    ], [
        InlineKeyboardButton('Try me inline!', switch_inline_query_current_chat='')
    ]]
    return InlineKeyboardMarkup(buttons)
