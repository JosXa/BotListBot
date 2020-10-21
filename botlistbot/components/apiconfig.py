import logging
import re
from pprint import pprint

import datetime
import emoji
from telegram import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup, TelegramError
from telegram.ext import ConversationHandler

from botlistbot import captions
from botlistbot import const
from botlistbot import mdformat
from botlistbot import util
from botlistbot.util import private_chat_only
from main import log
from botlistbot.const import *
from botlistbot.const import BotStates, CallbackActions
from botlistbot.custemoji import Emoji
from botlistbot.models import Bot
from botlistbot.models import Category
from botlistbot.models import Suggestion
from botlistbot.util import restricted

logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.INFO)
log = logging.getLogger(__name__)


# @private_chat_only
# def webhook(bot, update):
#     update.message.reply_text(
#         util.action_hint("Please enter an URL where you want to be notified about updates of the @BotList"))
#     return BotStates.EXPECTING_WEBHOOK_URL
#
#
# def set_webhook(bot, update):
#     text = update.message.text
#
#     update.message.reply_text(
#         util.action_hint("Webhook set."))
#     return ConversationHandler.END

