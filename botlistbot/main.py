# -*- coding: utf-8 -*-
import sentry_sdk
import threading
import logging
import time

from decouple import config
from logzero import logger as log
from sentry_sdk.integrations.logging import LoggingIntegration
from telegram import Bot as TelegramBot, TelegramError
from telegram.ext import Updater
from telegram.utils.request import Request

import appglobals
import routing
import settings
import util
from components import admin, basic
from lib.markdownformatter import MarkdownFormatter


class BotListBot(TelegramBot):
    def send_notification(self, message, **kwargs):
        self.send_message(
            settings.BOTLIST_NOTIFICATIONS_ID,
            util.escape_markdown(message),
            parse_mode='markdown',
            timeout=20,
            **kwargs
        )
        log.info(message)

    def delete_message(self, chat_id, message_id, timeout=None, safe=False, **kwargs):
        if not safe:
            return super().delete_message(chat_id, message_id, timeout, **kwargs)
        try:
            return super().delete_message(chat_id, message_id, timeout, **kwargs)
        except TelegramError:
            return None


def setup_logging():
    sentry_logging = LoggingIntegration(
        level=logging.INFO,  # Capture info and above as breadcrumbs
        event_level=logging.WARNING,  # Send errors as events
    )
    sentry_sdk.init(
        settings.SENTRY_URL,
        integrations=[sentry_logging],
        environment=settings.SENTRY_ENVIRONMENT
    )


def main():
    # Start API
    # thread = threading.Thread(target=botlistapi.start_server)
    # thread.start()
    if settings.is_sentry_enabled():
        sentry_sdk.init(settings.SENTRY_URL, environment=settings.SENTRY_ENVIRONMENT)

    botchecker_context = {}

    bot_token = str(settings.BOT_TOKEN)

    botlistbot = BotListBot(bot_token, request=Request(
        read_timeout=8,
        connect_timeout=7,
        con_pool_size=settings.WORKER_COUNT + 4
    ))
    updater = Updater(
        bot=botlistbot,
        workers=settings.WORKER_COUNT,
    )
    # updater.dispatcher = BotListDispatcher(
    #     botlistbot,
    #     updater.update_queue,
    #     job_queue=updater.job_queue,
    #     workers=settings.WORKER_COUNT,
    #     exception_event=threading.Event())

    botlistbot.formatter = MarkdownFormatter(updater.bot)

    # Get the dispatcher to on_mount handlers
    dp = updater.dispatcher

    # message_queue = MessageQueue()
    # message_queue._is_messages_queued_default = True
    # updater.bot._is_messages_queued_default = True
    # updater.bot._msg_queue = message_queue
    # updater.bot.queuedmessage = messagequeue.queuedmessage
    # updater.bot.send_message = updater.bot.queuedmessage(updater.bot.send_message)

    routing.register(dp, None)
    basic.register(dp)

    updater.job_queue.run_repeating(admin.last_update_job, interval=3600 * 24)

    if settings.DEV:
        log.info("Starting using long polling...")
        updater.start_polling()
    else:
        log.info("Starting using webhooks...")
        updater.start_webhook(listen="0.0.0.0",
                              port=settings.PORT,
                              url_path=settings.BOT_TOKEN)
        updater.bot.set_webhook(f"https://botlistbot.herokuapp.com/{settings.BOT_TOKEN}")

    log.info('Listening...')
    updater.bot.send_message(settings.DEVELOPER_ID, "Ready to rock", timeout=10)

    # Idling
    updater.idle()
    updater.stop()

    log.info('Disconnecting...')


if __name__ == '__main__':
    main()
