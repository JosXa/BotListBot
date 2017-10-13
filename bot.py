# -*- coding: utf-8 -*-
import logging
import os
import sys
import threading
from signal import signal, SIGINT, SIGTERM, SIGABRT

import time
from gevent.threading import Thread

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
from telegram.ext import Updater


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


setup_logger()
log = logging.getLogger(__name__)

botchecker_context = None


def signal_handler():
    log.info("Signaling stop to all jobs")
    botchecker_context.get('stop').set()


def main():
    # Start API
    thread = Thread(target=botlistapi.start_server)
    thread.start()

    bot_token = str(sys.argv[1])

    updater = Updater(bot_token, workers=settings.WORKER_COUNT)
    updater.bot.formatter = MarkdownFormatter(updater.bot)

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

    # Start Userbot
    if settings.RUN_BOTCHECKER:
        api_id = 34057
        api_hash = 'a89154bb0cde970cae0848dc7f7a6108'
        phone = '+79639953313'
        session_file = settings.USERBOT_SESSION  # botchecker
        bot_checker = BotChecker(session_file, api_id, api_hash, phone, updater)

        global botchecker_context
        botchecker_context = {'checker': bot_checker, 'stop': threading.Event()}
        # updater.job_queue.run_repeating(
        #     botchecker.job_callback, context=botchecker_context,
        #     first=5,
        #     interval=3600 * 2)

    updater.job_queue.run_repeating(admin.last_update_job, interval=3600 * 24)
    updater.start_polling()

    log.info('Listening...')
    updater.bot.send_message(settings.ADMINS[0], "Ready to rock")

    # Idling
    updater.idle()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        signal_handler()
        updater.stop()
        log.info('Disconnecting...')
        appglobals.disconnect()


if __name__ == '__main__':
    main()
