import captions
import const
import util
from telegram import ParseMode

from telegram import InlineKeyboardButton

from telegram import InlineKeyboardMarkup
from telegram.ext import ConversationHandler

import helpers
import messages
from util import track_groups


def available_commands(bot, update):
    update.message.reply_text('*Available commands:*\n' + helpers.get_commands(), parse_mode=ParseMode.MARKDOWN)


@track_groups
def help(bot, update):
    reply_markup = InlineKeyboardMarkup(
        [[InlineKeyboardButton('Try me inline!', switch_inline_query_current_chat='')]])
    update.message.reply_text(messages.HELP_MESSAGE_ENGLISH, quote=False, parse_mode=ParseMode.MARKDOWN,
                              reply_markup=reply_markup)
    return ConversationHandler.END


def _reroute_private_chat(update, quote, action, message):
    if util.is_group_message(update):
        update.message.reply_text(
            messages.REROUTE_PRIVATE_CHAT,
            quote=quote,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton(
                    captions.SWITCH_PRIVATE,
                    url="https://t.me/{}?start={}".format(
                        const.SELF_BOT_NAME,
                        action)),
                    InlineKeyboardButton('Switch to inline', switch_inline_query=action)
                ]]
            ))
    else:
        update.message.reply_text(message, quote=quote, parse_mode=ParseMode.MARKDOWN)


def contributing(bot, update, quote=True):
    _reroute_private_chat(update, quote, const.DeepLinkingActions.CONTRIBUTING, messages.CONTRIBUTING)
    return ConversationHandler.END


def examples(bot, update, quote=True):
    _reroute_private_chat(update, quote, const.DeepLinkingActions.EXAMPLES, messages.EXAMPLES)
    return ConversationHandler.END


def rules(bot, update, quote=True):
    chat_id = util.cid_from_update(update)
    if chat_id == const.BOTLISTCHAT_ID or util.is_private_message(update):
        _reroute_private_chat(update, quote, const.DeepLinkingActions.RULES, messages.BOTLISTCHAT_RULES)
    else:
        update.message.reply_text("Sorry, but I don't know the rules in this group 👻\n\n" + messages.PROMOTION_MESSAGE,
                                  parse_mode=ParseMode.MARKDOWN)
    return ConversationHandler.END
