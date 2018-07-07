from mdformat import success, failure, action_hint
from telegram import Message, constants, Bot
from telegram import ParseMode
from telegram import ReplyKeyboardRemove
from telegram.error import BadRequest


class MarkdownFormatter:
    def __init__(self, bot: Bot, message_id: int=None):
        self.bot = bot
        self.message_id = message_id

    @staticmethod
    def _set_defaults(kwargs):
        if 'disable_web_page_preview' not in kwargs:
            kwargs['disable_web_page_preview'] = True
        if 'parse_mode' not in kwargs:
            kwargs['parse_mode'] = ParseMode.MARKDOWN
        return kwargs

    def send_message(self, chat_id, text: str, **kwargs):
        if len(text) <= constants.MAX_MESSAGE_LENGTH:
            return self.bot.sendMessage(chat_id, text, **self._set_defaults(kwargs))

        parts = []
        while len(text) > 0:
            if len(text) > constants.MAX_MESSAGE_LENGTH:
                part = text[:constants.MAX_MESSAGE_LENGTH]
                first_lnbr = part.rfind('\n')
                parts.append(part[:first_lnbr])
                text = text[first_lnbr:]
            else:
                parts.append(text)
                break

        msg = None
        for part in parts:
            msg = self.bot.sendMessage(chat_id, part, **self._set_defaults(kwargs))
        return msg

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

    def send_or_edit(self, chat_id, text, **kwargs):

        try:
            if self.message_id:
                return self.bot.edit_message_text(
                    text,
                    chat_id=chat_id,
                    message_id=self.message_id,
                    **self._set_defaults(kwargs)
                )

            return self.send_message(chat_id, text=text, **self._set_defaults(kwargs))
        except BadRequest as e:
            if 'not modified' in e.message.lower():
                pass
            else:
                return self.send_message(chat_id, text=text, **self._set_defaults(kwargs))
