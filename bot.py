# -*- coding: utf-8 -*-
import logging
import os
import sys

from gevent.threading import Thread
from telegram.ext import Updater

import appglobals
import routing
import settings
from api import botlistapi
from components import _playground
from components import admin
from components import basic
from components.userbot import botchecker
from components.userbot.botchecker import BotChecker
from lib.markdownformatter import MarkdownFormatter


### TODO ###
#
# - 💻🚦Developer and Monitoring Tools
#
#
#
#
###


def setup_logger():
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    if not os.path.exists(settings.LOG_DIR):
        os.makedirs(settings.LOG_DIR)

    console_formatter = logging.Formatter("%(name)-12s: %(levelname)-8s %(message)s")
    file_formatter = logging.Formatter(
        "[%(asctime)s] {%(pathname)s:%(lineno)d} %(levelname)s - %(message)s")

    # create console handler and set level to info
    handler = logging.StreamHandler()
    handler.setLevel(logging.INFO)
    handler.setFormatter(console_formatter)
    logger.addHandler(handler)

    # create error file handler and set level to error
    handler = logging.FileHandler(settings.ERROR_LOG_FILE, "w", encoding=None, delay="true")
    handler.setLevel(logging.ERROR)
    handler.setFormatter(file_formatter)
    logger.addHandler(handler)

    # create debug file handler and set level to debug
    handler = logging.FileHandler(settings.DEBUG_LOG_FILE, "w", encoding=None, delay="true")
    handler.setLevel(logging.DEBUG)
    handler.setFormatter(file_formatter)
    logger.addHandler(handler)


def main():
    setup_logger()
    log = logging.getLogger(__name__)

    # Start API
    thread = Thread(target=botlistapi.start_server)
    thread.start()

    bot_token = str(sys.argv[1])

    updater = Updater(bot_token, workers=settings.WORKER_COUNT)
    updater.bot.formatter = MarkdownFormatter(updater.bot)

    # Start Userbot
    api_id = 34057
    api_hash = 'a89154bb0cde970cae0848dc7f7a6108'
    phone = '+79639953313'
    bot_checker = BotChecker('botchecker', api_id, api_hash, phone, updater)

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # message_queue = MessageQueue()
    # message_queue._is_messages_queued_default = True
    # updater.bot._is_messages_queued_default = True
    # updater.bot._msg_queue = message_queue
    # updater.bot.queuedmessage = messagequeue.queuedmessage
    # updater.bot.send_message = updater.bot.queuedmessage(updater.bot.send_message)

    routing.register(dp)
    basic.register(dp)
    _playground.register(dp)

    # JOBS
    updater.job_queue.run_repeating(admin.last_update_job, interval=3600 * 24)
    updater.job_queue.run_repeating(botchecker.job_callback, context=bot_checker, first=0,
                                    interval=3600 * 2)

    updater.start_polling()

    log.info('Listening...')
    updater.bot.send_message(settings.ADMINS[0], "Ready to rock")
    updater.idle()

    log.info('Disconnecting...')
    appglobals.disconnect()


if __name__ == '__main__':
    main()
