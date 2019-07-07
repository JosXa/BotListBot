import asyncio

import settings
from logzero import logger as log

if settings.USE_USERBOT:
    from components.userbot import botchecker
    from components.userbot.botchecker import BotChecker

    bot_checker = BotChecker(
        event_loop=asyncio.get_event_loop(),
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
            pass
            # botchecker_context.update(
            #     {'checker': bot_checker, 'stop': threading.Event()})
            # updater.job_queue.run_repeating(
            #     botchecker.ping_bots_job,
            #     context=botchecker_context,
            #     first=1.5,
            #     interval=settings.BOTCHECKER_INTERVAL
            # )

    # threading.Thread(target=start_userbot, name="BotChecker").start()

