# -*- coding: utf-8 -*-

import sentry_sdk
import logging

from logzero import logger as log
from sentry_sdk.integrations.logging import LoggingIntegration
from telegram.ext import Updater, JobQueue
from telegram.utils.request import Request

from botlistbot import appglobals
from botlistbot import routing
from botlistbot import settings
from botlistbot.components import admin, basic
from botlistbot.custom_botlistbot import BotListBot
from botlistbot.lib.markdownformatter import MarkdownFormatter


def setup_logging():
    sentry_logging = LoggingIntegration(
        level=logging.INFO,  # Capture info and above as breadcrumbs
        event_level=logging.WARNING,  # Send errors as events
    )
    sentry_sdk.init(
        settings.SENTRY_URL,
        integrations=[sentry_logging],
        environment=settings.SENTRY_ENVIRONMENT,
    )


def main():
    # Start API
    # thread = threading.Thread(target=botlistapi.start_server)
    # thread.start()
    if settings.is_sentry_enabled():
        sentry_sdk.init(settings.SENTRY_URL, environment=settings.SENTRY_ENVIRONMENT)

    botchecker_context = {}

    bot_token = str(settings.BOT_TOKEN)

    botlistbot = BotListBot(
        bot_token,
        request=Request(
            read_timeout=8,
            connect_timeout=7,
            con_pool_size=max(settings.WORKER_COUNT, 4),
        ),
    )
    updater = Updater(bot=botlistbot, workers=settings.WORKER_COUNT)

    botlistbot.formatter = MarkdownFormatter(updater.bot)

    appglobals.job_queue = updater.job_queue

    # Get the dispatcher to on_mount handlers
    dp = updater.dispatcher

    routing.register(dp, None)
    basic.register(dp)

    updater.job_queue.run_repeating(admin.last_update_job, interval=3600 * 24)

    if settings.DEV:
        log.info("Starting using long polling...")
        updater.start_polling()
    else:
        log.info("Starting using webhooks...")
        updater.start_webhook(
            listen="0.0.0.0", port=settings.PORT, url_path=settings.BOT_TOKEN
        )
        updater.bot.set_webhook(
            f"https://botlistbot.herokuapp.com/{settings.BOT_TOKEN}"
        )

    log.info("Listening...")
    updater.bot.send_message(settings.DEVELOPER_ID, "Ready to rock", timeout=10)

    # Idling
    updater.idle()
    updater.stop()

    log.info("Disconnecting...")


if __name__ == "__main__":
    main()
