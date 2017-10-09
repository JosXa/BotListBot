import traceback
from pprint import pprint

from telegram import Message
from telegram import ParseMode
from telegram import ReplyKeyboardRemove
from telegram.error import BadRequest

from mdformat import success, failure, action_hint


class MarkdownFormatter:
    def __init__(self, bot):
        self.bot = bot

    def _set_defaults(self, kwargs):
        if 'disable_web_page_preview' not in kwargs:
            kwargs['disable_web_page_preview'] = True
        if 'parse_mode' not in kwargs:
            kwargs['parse_mode'] = ParseMode.MARKDOWN
        return kwargs

    def send_message(self, chat_id, text: str, **kwargs):
        return self.bot.sendMessage(chat_id, text, **self._set_defaults(kwargs))

    def send_success(self, chat_id, text: str, add_punctuation=True, reply_markup=None, **kwargs):
        if add_punctuation:
            if text[-1] != '.':
                text += '.'

        if not reply_markup:
            reply_markup = ReplyKeyboardRemove()
        return self.bot.sendMessage(
            chat_id,
            success(text),
            reply_markup=reply_markup,
            **self._set_defaults(kwargs))

    def send_failure(self, chat_id, text: str, **kwargs):
        text = str.strip(text)
        if text[-1] != '.':
            text += '.'
        return self.bot.sendMessage(
            chat_id,
            failure(text),
            **self._set_defaults(kwargs))

    def send_action_hint(self, chat_id, text: str, **kwargs):
        if text[-1] == '.':
            text = text[0:-1]
        return self.bot.sendMessage(
            chat_id,
            action_hint(text),
            **self._set_defaults(kwargs))

    def send_or_edit(self, chat_id, text, to_edit=None, **kwargs):
        mid = to_edit
        if isinstance(to_edit, Message):
            mid = to_edit.message_id

        try:
            if to_edit:
                return self.bot.edit_message_text(
                    text,
                    chat_id=chat_id,
                    message_id=mid,
                    **self._set_defaults(kwargs)
                )

            return self.send_message(chat_id, text=text, **self._set_defaults(kwargs))
        except BadRequest as e:
            if 'not modified' in e.message.lower():
                pass
            else:
                return self.send_message(chat_id, text=text, **self._set_defaults(kwargs))
