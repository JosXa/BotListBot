#!/usr/bin/python3
from collections import Counter

import asyncio
import asyncpool
import filecmp
import logging
import os
import re
import shutil
import time
import traceback
from datetime import datetime, timedelta
from logzero import logger as log
from pyrogram.api.errors import FloodWait, QueryTooShort, UnknownError, UsernameInvalid, \
    UsernameNotOccupied
from pyrogram.api.functions.contacts import Search
from pyrogram.api.functions.messages import DeleteHistory
from pyrogram.api.functions.users import GetUsers
from pyrogram.api.types import InputPeerUser
from pyrogram.api.types.contacts import ResolvedPeer
from telegram import Bot as TelegramBot, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import BadRequest

import captions
import helpers
import settings
import util
from const import CallbackActions
from helpers import make_sticker
from model import Bot as BotModel, Keyword
from tgintegration import InteractionClientAsync, Response

logging.getLogger().setLevel(logging.WARNING)

ZERO_CHAR1 = u"\u200C"  # ZERO-WIDTH-NON-JOINER
ZERO_CHAR2 = u"\u200B"  # ZERO-WIDTH-SPACE
botbuilder_pattern = re.compile('|'.join(settings.BOTBUILDER_DETERMINERS), re.IGNORECASE)
offline_pattern = re.compile('|'.join(settings.OFFLINE_DETERMINERS), re.IGNORECASE)

TMP_DIR = os.path.join(settings.BOT_THUMBNAIL_DIR, "tmp")
if os.path.exists(TMP_DIR):
    shutil.rmtree(TMP_DIR)
os.makedirs(TMP_DIR)


# class Stats:
#     def __init__(self, filepath):
#         _counter_file = Path(filepath).expanduser()
#         os.makedirs(_counter_file.parent, exist_ok=True)
#         _counter_file.touch()
#
#         self.store = shelve.open(str(_counter_file), writeback=True)
#
#         self.store.setdefault("sent_messages", 0)
#         self.store.setdefault("tracking_start", datetime.now())
#
#     def incr_count(self):
#         sent_messages = self.store["sent_messages"]
#         if sent_messages > 8000:
#             raise StopBotchecker
#         self.store["sent_messages"] = sent_messages + 1
#
#
# class StopBotchecker(Exception):
#     """ Raised when botchecker is over limit """
#
#
# stats = Stats('~/.run/botlistbot/botchecker-stats.json')

def zero_width_encoding(encoded_string):
    if not encoded_string:
        return None
    result = ''
    for c in encoded_string:
        if c in (ZERO_CHAR1, ZERO_CHAR2):
            result += c
        else:
            return result
    return None


class BotChecker(InteractionClientAsync):
    def __init__(self, event_loop, session_name, api_id, api_hash, phone_number):

        self.event_loop = event_loop
        self.username_flood_until = None
        self._message_intervals = {}
        self._last_ping = None
        self.__photos_lock = asyncio.Lock(loop=self.event_loop)

        super(BotChecker, self).__init__(
            session_name,
            api_id,
            api_hash,
            workers=4,
            phone_number=phone_number,
        )
        self.logger.setLevel(logging.WARNING)

    async def schedule_conversation_deletion(self, peer, delay=5):
        await asyncio.sleep(delay)
        self.send(DeleteHistory(self.resolve_peer(peer), max_id=999999999, just_clear=True))
        log.debug("Deleted conversation with {}".format(peer))

    # def delete_all_conversations(self):
    #     all_peers = [utils.resolve_id(x[0]) for x in self.session.entities.get_input_list()]
    #     for peer in all_peers:
    #         log.debug("Deleting conversation with {}...".format(peer))
    #         try:
    #             input_entity = self.client.session.entities.get_input_entity(peer[0])
    #             self.client(DeleteHistoryRequest(input_entity, max_id=9999999999999999))
    #         except:
    #             log.error("Couldn't find {}".format(peer[0]))

    def update_bot_details(self, to_check: BotModel, peer):
        """
        Set basic properties of the bot
        """
        user = None

        if isinstance(peer, ResolvedPeer):
            peer = self.resolve_peer(peer.peer.user_id)
        elif isinstance(peer, InputPeerUser):
            pass
        else:
            peer = self.resolve_peer(peer.id)

        if not user:
            try:
                user = self.send(GetUsers([peer]))[0]
            except:
                traceback.print_exc()
                print("this peer does not work for GetUsers:")
                print(type(peer))
                print(peer)
                return None

        if hasattr(user, 'bot') and user.bot is True:
            # Regular bot
            to_check.official = bool(user.verified)
            to_check.inlinequeries = bool(user.bot_inline_placeholder)
            to_check.name = user.first_name
            to_check.bot_info_version = user.bot_info_version
        else:
            # Userbot
            to_check.userbot = True
            to_check.name = helpers.format_name(user)

        # In any case
        to_check.chat_id = int(user.id)
        to_check.username = '@' + str(user.username)

    # def send_message(self, *args, **kwargs):
    #     timeout_between_sends = 0.5
    #     if self._last_ping:
    #         diff = timeout_between_sends - (time.time() - self._last_ping)
    #         if diff > 0:
    #             time.sleep(diff)
    #
    #     result = super(BotChecker, self).send_message(*args, **kwargs)
    #     self._last_ping = time.time()
    #     return result

    async def get_ping_response(self, peer, timeout=30, try_inline=True):
        response = await self.ping_bot(
            peer,
            override_messages=settings.PING_MESSAGES,
            max_wait_response=timeout,
            raise_=False
        )
        if response.empty:
            return False

        # Evaluate WJClub's ParkMeBot flags
        reserved_username = ZERO_CHAR1 + ZERO_CHAR1 + ZERO_CHAR1 + ZERO_CHAR1
        parked = ZERO_CHAR1 + ZERO_CHAR1 + ZERO_CHAR1 + ZERO_CHAR2
        maintenance = ZERO_CHAR1 + ZERO_CHAR1 + ZERO_CHAR2 + ZERO_CHAR1

        full_text = response.full_text
        if zero_width_encoding(full_text) in (reserved_username, parked, maintenance):
            return False
        if offline_pattern.search(full_text):
            return False

        return response

    def resolve_bot(self, bot: BotModel):
        if bot.chat_id:
            try:
                return self.resolve_peer(bot.chat_id)
            except:
                pass

        try:
            results = self.send(Search(bot.username, limit=3))
            if results.users:
                try:
                    return next(
                        s for s in results.users if s.username.lower() == bot.username[1:].lower())
                except StopIteration:
                    pass
        except QueryTooShort:
            log.error("QueryTooShort: {}".format(bot.username))

        if self.username_flood_until:
            if self.username_flood_until < datetime.now():
                self.username_flood_until = None
        else:
            try:
                return self.resolve_peer(bot.username)
            except FloodWait as e:
                self.username_flood_until = datetime.now() + timedelta(
                    seconds=e.x)
                log.warning("Flood wait for ResolveUsername: {}s (until {})".format(
                    e.x, self.username_flood_until))
            except UsernameInvalid as e:
                log.error(e)  # TODO

        return None

    async def download_profile_photo(self, bot: BotModel, photo_path):
        tmp_file = os.path.join(TMP_DIR, bot.username.replace('@', '') + '.jpg')
        photos = self.get_user_profile_photos(bot.chat_id).photos
        if photos:
            photo_size_object = photos[0][-1]

            await self.__photos_lock.acquire()
            try:
                try:
                    self.download_media(
                        photo_size_object,
                        file_name=tmp_file,
                        block=True
                    )
                except FloodWait as e:
                    # TODO: as the error happens inside of the update worker, this won't work (yet)
                    # Leaving it in as the default behavior should be to raise the FloodWait
                    # when block=True
                    log.debug(f"FloodWait for downloading media ({e.x})")

                if os.path.exists(tmp_file):
                    try:
                        similar = filecmp.cmp(tmp_file, photo_path, shallow=False)
                    except FileNotFoundError:
                        similar = False

                    if not similar:
                        shutil.copy(tmp_file, photo_path)
            finally:
                await self.__photos_lock.release()


async def check_bot(bot, bot_checker: BotChecker, to_check: BotModel, result_queue: asyncio.Queue):
    log.debug("Checking bot {}...".format(to_check.username))

    try:
        peer = bot_checker.resolve_bot(to_check)
    except UsernameNotOccupied:
        markup = InlineKeyboardMarkup([[
            InlineKeyboardButton(captions.EDIT_BOT, callback_data=util.callback_for_action(
                CallbackActions.EDIT_BOT,
                dict(id=to_check.id)
            ))
        ]])
        text = "{} does not exist (anymore). Please resolve this " \
               "issue manually!".format(to_check.username)
        try:
            bot.send_message(settings.BLSF_ID, text, reply_markup=markup)
        except BadRequest:
            bot.send_notification(text)
        return await result_queue.put('not found')

    if not peer:
        return await result_queue.put('skipped')

    bot_checker.update_bot_details(to_check, peer=peer)

    # Check online state
    try:
        response = await bot_checker.get_ping_response(
            to_check.chat_id,
            timeout=18,
            try_inline=to_check.inlinequeries)
    except UnknownError as e:
        result_queue.put(e.MESSAGE)
        return
    except Exception as e:
        log.exception(e)
        result_queue.put(str(e))
        return

    for _ in range(2):
        await result_queue.put('messages sent')

    was_offline = to_check.offline
    is_offline = not bool(response)

    now = datetime.now()
    to_check.last_ping = now
    if not is_offline:
        to_check.last_response = now

    if was_offline != is_offline:
        bot.send_message(settings.BOTLIST_NOTIFICATIONS_ID, '{} went {}.'.format(
            to_check.str_no_md,
            'offline' if to_check.offline else 'online'
        ), timeout=40)

    if isinstance(response, Response) and not response.empty:  # might also be bool
        # Search for botbuilder pattern to see if this bot is a Manybot/Chatfuelbot/etc.
        full_text = response.full_text.lower()
        if botbuilder_pattern.search(full_text):
            to_check.botbuilder = True

        # Search /start and /help response for global list of keywords
        to_add = []
        for name in Keyword.get_distinct_names(exclude_from_bot=to_check):
            if re.search(r'\b{}\b'.format(name), full_text, re.IGNORECASE):
                to_add.append(name)

        to_add = [x for x in to_add if x not in settings.FORBIDDEN_KEYWORDS]

        if to_add:
            for k in to_add:
                Keyword.insert(name=k, entity=to_check).execute()
                # s = Suggestion.add_or_update(
                #     user=User.botlist_user_instance(),
                #     action="add_keyword",
                #     subject=to_check,
                #     value=k
                # )
                # s.apply()
            # KeywordSuggestion.insert_many(
            #     [dict(name=x, entity=to_check) for x in to_add]
            # ).execute()
            msg = 'New keyword{}: {} for {}.'.format(
                's' if len(to_add) > 1 else '',
                ', '.join(['#' + k for k in to_add]),
                to_check.str_no_md)
            bot.send_message(settings.BOTLIST_NOTIFICATIONS_ID, msg, timeout=40)
            log.info(msg)

    # Download profile picture
    if settings.DOWNLOAD_PROFILE_PICTURES:
        photo_file = to_check.thumbnail_file
        sticker_file = os.path.join(settings.BOT_THUMBNAIL_DIR, '_sticker_tmp.webp')

        await bot_checker.download_profile_photo(to_check, photo_file)
        if settings.NOTIFY_NEW_PROFILE_PICTURE:
            make_sticker(photo_file, sticker_file)
            bot.send_notification("New profile picture of {}:".format(to_check.username))
            bot.send_sticker(settings.BOTLIST_NOTIFICATIONS_ID,
                             open(photo_file, 'rb'), timeout=360)

    to_check.save()

    if settings.DELETE_CONVERSATION_AFTER_PING:
        await bot_checker.schedule_conversation_deletion(to_check.chat_id, 10)

    await disable_decider(bot, to_check)

    await result_queue.put('offline' if to_check.offline else 'online')


async def result_reader(queue) -> Counter:
    stats = Counter()
    while True:
        value = await queue.get()
        if value is None:
            break
        stats.update([value])
    return stats


async def run(telegram_bot, bot_checker, bots) -> Counter:
    result_queue = asyncio.Queue()
    loop = bot_checker.event_loop
    reader_future = asyncio.ensure_future(result_reader(result_queue), loop=loop)

    # TODO: check correct order of bots concerning pings etc.

    async with asyncpool.AsyncPool(
            loop,
            num_workers=settings.BOTCHECKER_CONCURRENT_COUNT,
            name="BotChecker",
            logger=log,
            worker_co=check_bot,
            max_task_time=300,
            log_every_n=settings.BOTCHECKER_CONCURRENT_COUNT,
            expected_total=len(bots),
    ) as pool:
        for to_check in bots:
            await pool.push(telegram_bot, bot_checker, to_check, result_queue)

    await result_queue.put(None)
    return await reader_future


def ping_bots_job(bot, job):
    bot_checker = job.context.get('checker')
    loop = bot_checker.event_loop

    all_bots = BotModel.select(BotModel).where(
        (BotModel.approved == True)
        &
        ((BotModel.disabled_reason == BotModel.DisabledReason.offline) |
         BotModel.disabled_reason.is_null())
    ).order_by(
        BotModel.last_ping.asc()
    )

    start = time.time()
    result = loop.run_until_complete(run(bot, bot_checker, all_bots))  # type: Counter
    end = time.time()

    if not result:
        msg = "👎 BotChecker encountered problems."
    else:
        msg = "ℹ️ BotChecker completed in {}s:\n".format(round(end - start))
        for k, v in result.items():
            msg += "\n● {} {}".format(v, k)
    bot.send_message(settings.BOTLIST_NOTIFICATIONS_ID, msg)
    log.info(msg)


async def disable_decider(bot: TelegramBot, to_check: BotModel):
    assert to_check.disabled_reason != BotModel.DisabledReason.banned

    if (
            to_check.offline and
            to_check.offline_for > settings.DISABLE_BOT_INACTIVITY_DELTA and
            to_check.disabled_reason != BotModel.DisabledReason.offline
    ):
        # Disable if the bot has been offline for too long
        if to_check.disable(to_check.DisabledReason.offline):
            to_check.save()

            if to_check.last_response:
                reason = "its last response was " + helpers.slang_datetime(to_check.last_response)
            else:
                reason = "it's been offline for.. like... ever"

            msg = "❌ {} disabled as {}.".format(to_check, reason)
            log.info(msg)
            bot.send_message(settings.BOTLIST_NOTIFICATIONS_ID, msg, timeout=30,
                             parse_mode='markdown')
        else:
            log.info("huhwtf")
    elif (
            to_check.online and
            to_check.disabled_reason == BotModel.DisabledReason.offline
    ):
        # Re-enable if the bot is disabled and came back online
        if to_check.enable():
            to_check.save()
            msg = "{} was included in the @BotList again as it came back online.".format(to_check)
            log.info(msg)
            bot.send_message(settings.BOTLIST_NOTIFICATIONS_ID, msg, timeout=30,
                             parse_mode='markdown')
        else:
            log.info("huhwtf")
