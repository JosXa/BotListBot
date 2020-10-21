from telegram.error import BadRequest
from typing import Callable

from logzero import logger as log
from telegram import Bot as TelegramBot, TelegramError

from botlistbot import settings
from botlistbot import util


class BotListBot(TelegramBot):
    def send_notification(self, message, **kwargs):
        self.send_message(
            settings.BOTLIST_NOTIFICATIONS_ID,
            util.escape_markdown(message),
            parse_mode="markdown",
            timeout=20,
            **kwargs,
        )
        log.info(message)

    def _wrap_safe(self, action: Callable, safe: bool):
        if not safe:
            return action()
        try:
            return action()
        except BadRequest:
            return None

    def answer_inline_query(
            self,
            inline_query_id,
            results,
            cache_time=300,
            is_personal=None,
            next_offset=None,
            switch_pm_text=None,
            switch_pm_parameter=None,
            timeout=None,
            safe=True,
            **kwargs,
    ):
        return self._wrap_safe(
            lambda: super(BotListBot, self).answer_inline_query(
                inline_query_id,
                results,
                cache_time,
                is_personal,
                next_offset,
                switch_pm_text,
                switch_pm_parameter,
                timeout,
                **kwargs,
            ),
            safe=safe
        )

    def delete_message(self, chat_id, message_id, timeout=None, safe=False, **kwargs):
        return self._wrap_safe(
            lambda: super(BotListBot, self).delete_message(chat_id, message_id, timeout, **kwargs),
            safe=safe
        )