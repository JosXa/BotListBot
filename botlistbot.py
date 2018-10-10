from logzero import logger as log

import settings
import util
from mdformat import success, failure, action_hint
from telegram import Bot as TelegramBot, ParseMode, constants, ReplyKeyboardRemove
from telegram.error import BadRequest


class BotListBot(TelegramBot):

    def __init__(self, token, base_url=None, base_file_url=None, request=None, private_key=None,
                 private_key_password=None, callback_manager=None):
        super().__init__(token, base_url, base_file_url, request, private_key, private_key_password)
        self.callback_manager = callback_manager

    @staticmethod
    def _set_defaults(kwargs):
        if 'disable_web_page_preview' not in kwargs:
            kwargs['disable_web_page_preview'] = True
        if 'parse_mode' not in kwargs:
            kwargs['parse_mode'] = ParseMode.MARKDOWN
        return kwargs

    def send_message(self, chat_id, text: str, **kwargs):
        if len(text) <= constants.MAX_MESSAGE_LENGTH:
            return super().send_message(chat_id, text, **self._set_defaults(kwargs))

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
            msg = super().send_message(chat_id, part, **self._set_defaults(kwargs))
        return msg

    def send_notification(self, message, **kwargs):
        self.send_message(
            settings.BOTLIST_NOTIFICATIONS_ID,
            util.escape_markdown(message),
            parse_mode='markdown',
            timeout=20,
            **kwargs
        )
        log.info(message)

    def send_success(self, chat_id, text: str, add_punctuation=True, reply_markup=None, **kwargs):
        if add_punctuation:
            if text[-1] != '.':
                text += '.'

        if not reply_markup:
            reply_markup = ReplyKeyboardRemove()
        return self.send_message(
            chat_id,
            success(text),
            reply_markup=reply_markup,
            **self._set_defaults(kwargs))

    def send_failure(self, chat_id, text: str, **kwargs):
        text = str.strip(text)
        if text[-1] != '.':
            text += '.'
        return self.send_message(
            chat_id,
            failure(text),
            **self._set_defaults(kwargs))

    def send_action_hint(self, chat_id, text: str, **kwargs):
        if text[-1] == '.':
            text = text[0:-1]
        return self.send_message(
            chat_id,
            action_hint(text),
            **self._set_defaults(kwargs))

    def send_or_edit(self, chat_id, text, to_edit, **kwargs):

        try:
            if to_edit:
                return self.edit_message_text(
                    text,
                    chat_id=chat_id,
                    message_id=to_edit,
                    **self._set_defaults(kwargs)
                )

            return self.send_message(chat_id, text=text, **self._set_defaults(kwargs))
        except BadRequest as e:
            if 'not modified' in e.message.lower():
                pass
            else:
                return self.send_message(chat_id, text=text, **self._set_defaults(kwargs))