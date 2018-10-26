# -*- coding: utf-8 -*-
import flow
import threading
import time
from logzero import logger as log
from multiprocessing import Process
from signal import SIGABRT, SIGINT, SIGTERM, signal

from botlistbot import BotListBot
import appglobals
import routing
import settings
from components import admin
from components.userbot import botchecker
from components.userbot.botchecker import BotChecker
from lib import context
from lib.markdownformatter import MarkdownFormatter
from telegram.ext import Updater, PicklePersistence
from flow import DictCallbackManager
from telegram.utils.request import Request


class BotListUpdater(Updater):

    def __init__(self, token=None, base_url=None, workers=4, bot=None, private_key=None, private_key_password=None,
                 user_sig_handler=None, request_kwargs=None, persistence=None, use_context=False,
                 callback_manager=None):
        super().__init__(token, base_url, workers, bot, private_key, private_key_password, user_sig_handler,
                         request_kwargs, persistence, use_context)
        self.callback_manager = callback_manager


def main():
    # Start API
    # thread = threading.Thread(target=botlistapi.start_server)
    # thread.start()
    flow.patch()

    botchecker_context = {}

    persistence = PicklePersistence(filename=settings.PERSISTENCE_FILE)

    bot_token = settings.BOT_TOKEN

    callback_manager = DictCallbackManager()

    botlistbot = BotListBot(bot_token, request=Request(
        read_timeout=8,
        connect_timeout=7,
        con_pool_size=settings.WORKER_COUNT + 4,
    ), callback_manager=callback_manager)
    updater = BotListUpdater(
        bot=botlistbot,
        workers=settings.WORKER_COUNT,
        use_context=True,
        persistence=persistence,
        callback_manager=callback_manager
    )

    context.add_hooks()
    # updater.dispatcher = BotListDispatcher(
    #     botlistbot,
    #     updater.update_queue,
    #     job_queue=updater.job_queue,
    #     workers=settings.WORKER_COUNT,
    #     exception_event=threading.Event())

    # TODO: remove
    botlistbot.formatter = MarkdownFormatter(updater.bot)

    # Get the dispatcher to on_mount handlers
    dp = updater.dispatcher
    print(type(dp))

    # message_queue = MessageQueue()
    # message_queue._is_messages_queued_default = True
    # updater.bot._is_messages_queued_default = True
    # updater.bot._msg_queue = message_queue
    # updater.bot.queuedmessage = messagequeue.queuedmessage
    # updater.bot.send_message = updater.bot.queuedmessage(updater.bot.send_message)

    bot_checker = None
    bot_checker_process = None

    if settings.USE_USERBOT:
        bot_checker = BotChecker(
            event_loop=appglobals.loop,
            session_name=settings.USERBOT_SESSION,
            api_id=settings.API_ID,
            api_hash=settings.API_HASH,
            phone_number=settings.USERBOT_PHONE,
        )

        def start_userbot():
            log.info("Starting Userbot...")
            bot_checker.start()
            log.info("Userbot running.")

            if settings.RUN_BOTCHECKER:
                botchecker_context.update(
                    {'checker': bot_checker, 'stop': threading.Event()})
                updater.job_queue.run_repeating(
                    botchecker.ping_bots_job,
                    context=botchecker_context,
                    first=1.5,
                    interval=settings.BOTCHECKER_INTERVAL
                )

        bot_checker_process = Process(target=start_userbot, name="BotChecker")
        bot_checker_process.start()

    routing.register(dp, bot_checker)

    updater.job_queue.run_repeating(admin.last_update_job, interval=3600 * 24)
    updater.start_polling()

    log.info('Listening...')
    updater.bot.send_message(settings.ADMINS[0], "Ready to rock", timeout=10)

    is_idle = True

    def signal_handler(self, signum, frame):
        if bot_checker_process:
            if bot_checker_process.is_alive():
                bot_checker_process.terminate()
            global is_idle
            is_idle = False

    # Idling
    stop_signals = (SIGINT, SIGTERM, SIGABRT)
    for sig in stop_signals:
        signal(sig, signal_handler)

    while is_idle:
        time.sleep(1)

    appglobals.disconnect()
    updater.stop()
    updater.dispatcher.stop()
    log.info('Disconnecting...')


if __name__ == '__main__':
    main()
