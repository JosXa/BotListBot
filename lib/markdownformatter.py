from mdformat import success, failure, action_hint
from telegram import Message, constants, Bot
from telegram import ParseMode
from telegram import ReplyKeyboardRemove
from telegram.error import BadRequest


class MarkdownFormatter:
    def __init__(self, bot: Bot, message_id: int=None):
        self.bot = bot
        self.message_id = message_id

