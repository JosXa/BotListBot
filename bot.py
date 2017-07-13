# -*- coding: utf-8 -*-
import logging
import os
import sys

from telegram.ext import Updater
from telegram.ext import messagequeue
from telegram.ext.messagequeue import MessageQueue

import appglobals
import routing
from components import _playground
from components import admin
from components import basic
from lib.markdownformatter import MarkdownFormatter

logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.INFO)
log = logging.getLogger(__name__)


def main():
    # #TODO Start BotList API
    # thread = Thread(target=botlistapi.start_server)
    # thread.start()

    try:
        bot_token = str(os.environ['TG_TOKEN'])
    except Exception:
        bot_token = str(sys.argv[1])

    updater = Updater(bot_token, workers=20)
    updater.bot.formatter = MarkdownFormatter(updater.bot)

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    message_queue = MessageQueue()
    updater.bot._is_messages_queued_default = True
    updater.bot._msg_queue = message_queue
    updater.bot.queuedmessage = messagequeue.queuedmessage
    updater.bot.send_message = updater.bot.queuedmessage(updater.bot.send_message)

    routing.register(dp)
    basic.register(dp)
    _playground.register(dp)

    # JOBS
    # updater.job_queue.put(Job(channel_checker_job, TIME), next_t=0)
    updater.job_queue.run_repeating(admin.last_update_job, interval=60 * 60 * 24)  # 60*60

    updater.start_polling()

    log.info('Listening...')
    updater.idle()

    log.info('Disconnecting...')
    appglobals.disconnect()


if __name__ == '__main__':
    main()
