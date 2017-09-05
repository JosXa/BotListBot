import captions
import const
import helpers
import settings
import util
from dialog import messages
from helpers import reroute_private_chat
from telegram import InlineKeyboardButton
from telegram import InlineKeyboardMarkup
from telegram import ParseMode
from telegram.ext import ConversationHandler
from util import track_groups


def available_commands(bot, update):
    update.message.reply_text('*Available commands:*\n' + helpers.get_commands(), parse_mode=ParseMode.MARKDOWN)


@track_groups
def help(bot, update):
    mid = util.mid_from_update(update)
    cid = update.effective_chat.id
    bot.formatter.send_or_edit(cid, messages.HELP_MESSAGE_ENGLISH, to_edit=mid, reply_markup=_help_markup())
    return ConversationHandler.END


def contributing(bot, update, quote=True):
    mid = util.mid_from_update(update)
    cid = update.effective_chat.id
    bot.formatter.send_or_edit(cid, messages.CONTRIBUTING, to_edit=mid, reply_markup=_help_markup())
    return ConversationHandler.END


def examples(bot, update, quote=True):
    mid = util.mid_from_update(update)
    cid = update.effective_chat.id
    bot.formatter.send_or_edit(cid, messages.EXAMPLES, to_edit=mid, reply_markup=_help_markup())
    return ConversationHandler.END


def rules(bot, update, quote=True):
    chat_id = update.effective_chat.id
    if chat_id == settings.BOTLISTCHAT_ID or util.is_private_message(update):
        reroute_private_chat(bot, update, quote, const.DeepLinkingActions.RULES, messages.BOTLISTCHAT_RULES)
    else:
        update.message.reply_text("Sorry, but I don't know the rules in this group 👻\n\n" + messages.PROMOTION_MESSAGE,
                                  parse_mode=ParseMode.MARKDOWN)
    return ConversationHandler.END


def _help_markup():
    buttons = [[
        InlineKeyboardButton(captions.HELP, callback_data=util.callback_for_action(const.CallbackActions.HELP)),
        InlineKeyboardButton(captions.CONTRIBUTING,
                             callback_data=util.callback_for_action(const.CallbackActions.CONTRIBUTING)),
        InlineKeyboardButton(captions.EXAMPLES, callback_data=util.callback_for_action(const.CallbackActions.EXAMPLES)),
    ], [
        InlineKeyboardButton('Try me inline!', switch_inline_query_current_chat='')
    ]]
    return InlineKeyboardMarkup(buttons)
