import asyncio
import os
import threading
from pathlib import Path

from pyrogram import Client

import appglobals
import settings
from logzero import logger as log

from botcheckerworker.botchecker import BotChecker
from botcheckerworker.user_account_repository import download_session

download_session("josxa", appglobals.ACCOUNTS_DIR)

bot_checker = BotChecker(
    event_loop=asyncio.get_event_loop(),
    session_name=settings.USERBOT_SESSION,
    api_id=settings.API_ID,
    api_hash=settings.API_HASH,
    phone_number=settings.USERBOT_PHONE,
    workdir=appglobals.ACCOUNTS_DIR
)


async def start_userbot():
    log.info("Starting Userbot...")
    bot_checker.start()
    log.info("Userbot running.")

    await bot_checker.idle()

    if settings.RUN_BOTCHECKER:
        pass
        # botchecker_context.update(
        #     {'checker': bot_checker, 'stop': threading.Event()})
        # updater.job_queue.run_repeating(
        #     botcheckerworker.ping_bots_job,
        #     context=botchecker_context,
        #     first=1.5,
        #     interval=settings.BOTCHECKER_INTERVAL
        # )


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(start_userbot())
