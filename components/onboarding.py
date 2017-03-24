# -*- coding: utf-8 -*-
import logging
import re
from pprint import pprint

import datetime
import emoji
from telegram.ext import ConversationHandler, Job

import helpers
from model import User, Category
from telegram import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup, TelegramError

import captions
import const
import mdformat
import messages
import util
from bot import log, send_category, help, main_menu
from const import *
from const import BotStates, CallbackActions
from custemoji import Emoji
from model import Bot
from model import Category
from model import Keyword
from model import Suggestion
from util import restricted, track_groups

logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.INFO)
log = logging.getLogger(__name__)


@track_groups
def start(bot, update, args):
    tg_user = update.message.from_user
    chat_id = tg_user.id

    # Get or create the user from/in database
    user = User.from_telegram_object(tg_user)

    if len(args) > 0:
        # 1st arg: category id
        try:
            cat = Category.get(Category.id == args[0])
            return send_category(bot, update, cat)
        except Category.DoesNotExist:
            util.send_message_failure(bot, chat_id, "The requested category does not exist.")
        return
    help(bot, update)
    util.wait(bot, update)
    if util.is_private_message(update):
        main_menu(bot, update)
    return ConversationHandler.END