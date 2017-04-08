from telegram.ext import ConversationHandler

import captions
import const
import helpers
from helpers import reroute_private_chat
import messages
import util
from telegram import InlineKeyboardButton
from telegram import InlineKeyboardMarkup
from telegram import ParseMode
from util import track_groups


def available_commands(bot, update):
    update.message.reply_text('*Available commands:*\n' + helpers.get_commands(), parse_mode=ParseMode.MARKDOWN)


@track_groups
def help(bot, update):
    mid = util.mid_from_update(update)
    cid = util.cid_from_update(update)
    util.send_or_edit_md_message(bot, cid, messages.HELP_MESSAGE_ENGLISH, to_edit=mid, reply_markup=_help_markup())
    return ConversationHandler.END


def contributing(bot, update, quote=True):
    mid = util.mid_from_update(update)
    cid = util.cid_from_update(update)
    util.send_or_edit_md_message(bot, cid, messages.CONTRIBUTING, to_edit=mid, reply_markup=_help_markup())
    return ConversationHandler.END


def examples(bot, update, quote=True):
    mid = util.mid_from_update(update)
    cid = util.cid_from_update(update)
    util.send_or_edit_md_message(bot, cid, messages.EXAMPLES, to_edit=mid, reply_markup=_help_markup())
    return ConversationHandler.END


def rules(bot, update, quote=True):
    chat_id = util.cid_from_update(update)
    if chat_id == const.BOTLISTCHAT_ID or util.is_private_message(update):
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
