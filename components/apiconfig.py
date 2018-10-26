import logging
import re
from pprint import pprint

import datetime
import emoji
from telegram import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup, TelegramError
from telegram.ext import ConversationHandler

import captions
import const
import mdformat
import util
from util import private_chat_only
from main import log
from const import *
from const import BotStates, CallbackActions
from custemoji import Emoji
from models import Bot
from models import Category
from models import Suggestion
from util import restricted

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

