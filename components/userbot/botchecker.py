#!/usr/bin/python3
import datetime
import filecmp
import logging
import os
import shutil
import threading
import time
import traceback
from threading import Thread

from peewee import JOIN, fn

import settings
from helpers import make_sticker
from model import Bot as BotModel, Ping, Suggestion
from model import User as UserModel
from telegram import Bot as TelegramBot
from telegram import ForceReply
from telegram.ext import Filters, run_async
from telegram.ext import MessageHandler
from telethon import TelegramClient, utils
from telethon.errors import UsernameNotOccupiedError, FloodWaitError
from telethon.tl.functions.messages import DeleteHistoryRequest
from telethon.tl.types import User

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)

client_log = logging.getLogger(TelegramClient.__name__).setLevel(logging.DEBUG)

CONFIRM_PHONE_CODE = "Userbot authorization required. Enter the code you received..."
ZERO_CHAR1 = u"\u200C"  # ZERO-WIDTH-NON-JOINER
ZERO_CHAR2 = u"\u200B"  # ZERO-WIDTH-SPACE


class NotABotError(Exception):
    pass


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


def authorization_handler(bot, update, checker):
    text = update.message.reply_to_message.text
    if text == CONFIRM_PHONE_CODE:
        checker.authorize(update.message.text)


class BotChecker(object):
    def __init__(self, session_name, api_id, api_hash, phone_number, updater=None):
        self.phone_number = phone_number
        self.client = TelegramClient(session_name, api_id, api_hash, update_workers=4,
                                     spawn_read_thread=True, timeout=datetime.timedelta(seconds=15))
        self.client.connect()
        self._pinged_bots = []
        self._responses = {}
        self.botbuilders = []

        if not self.client.is_user_authorized():
            log.info("Sending code request...")
            self.client.send_code_request(phone_number)
            if updater:
                updater.bot.send_message(settings.ADMINS[0], CONFIRM_PHONE_CODE,
                                         reply_markup=ForceReply())
                updater.dispatcher.add_handler(MessageHandler(
                    Filters.reply & Filters.user(settings.ADMINS[0]),
                    lambda bot, update: authorization_handler(bot, update, self)),
                    group=3)
                self.pending_authorization = True
            else:
                self.client.send_code_request(phone_number)
                self.client.sign_in(phone_number, input('Enter code: '))
        else:
            self._initialize()

    def reset(self):
        self._pinged_bots = []
        self._responses = {}

    def authorize(self, code):
        self.client.sign_in(self.phone_number, code)
        self._initialize()

    def _initialize(self):
        self.pending_authorization = False
        self.client.add_update_handler(self._update_handler)

    def _update_handler(self, update):
        if update is None:
            log.error("Received `None` update.")
            return

        try:
            uid = update.message.from_id
        except AttributeError:
            try:
                uid = update.user_id
            except AttributeError:
                return

        # try:
        #     entity = self.client.get_entity(uid)
        #     log.debug("Received response from @{}".format(entity.username))
        # except:

        if uid in self._pinged_bots:
            log.debug("Received update from pinged bot {}: {}".format(uid, type(update)))
            message_text = None
            try:
                message_text = update.message.message
            except AttributeError:
                try:
                    message_text = update.message
                except AttributeError:
                    pass

            self._responses[uid] = message_text

    def _init_thread(self, target, *args, **kwargs):
        thr = Thread(target=target, args=args, kwargs=kwargs)
        thr.start()

    def schedule_conversation_deletion(self, peer, delay=5):
        def inner():
            time.sleep(delay)
            entity = self.client.get_input_entity(peer)
            self.client(DeleteHistoryRequest(entity, max_id=999999999))
            log.debug("Deleted conversation with {}".format(entity))

        thr = threading.Thread(target=inner, args=())
        thr.start()

    def delete_all_conversations(self):
        all_peers = [utils.resolve_id(x[0]) for x in self.client.session.entities.get_input_list()]
        for peer in all_peers:
            log.debug("Deleting conversation with {}...".format(peer))
            try:
                input_entity = self.client.session.entities.get_input_entity(peer[0])
                self.client(DeleteHistoryRequest(input_entity, max_id=9999999999999999))
            except:
                log.error("Couldn't find {}".format(peer[0]))

    def get_bot_entity(self, username) -> User:
        entity = self.client.get_entity(username)
        if not hasattr(entity, 'bot'):
            raise NotABotError("This user is not a bot.")
        time.sleep(15)  # ResolveUsernameRequests are expensive
        return entity

    def get_bot_entity_by_id(self, chat_id) -> User:
        entity = self.client.get_entity(chat_id)
        if not hasattr(entity, 'bot'):
            raise NotABotError("This user is not a bot.")
        return entity

    def _response_received(self, bot_user_id):
        return bot_user_id in [k for k in self._responses.keys()]

    def _delete_response(self, bot_user_id):
        del self._responses[bot_user_id]

    def ping_bot(self, entity, timeout=30):
        input_entity = utils.get_input_peer(entity)
        time.sleep(1)
        bot_user_id = input_entity.user_id

        self._pinged_bots.append(bot_user_id)
        log.debug('Pinging @{username}...'.format(
            username=entity.username))
        self.client.send_message(input_entity, '/start')

        start = datetime.datetime.now()
        help_attempted = False
        while not self._response_received(bot_user_id):
            if datetime.datetime.now() - start > datetime.timedelta(seconds=5) and \
                    not help_attempted:
                # Try sending /help if /start didn't work
                self.client.send_message(input_entity, '/help')
                help_attempted = True
            if datetime.datetime.now() - start > datetime.timedelta(seconds=timeout):
                # No response
                self._pinged_bots.remove(bot_user_id)
                log.debug('@{} did not respond after {} seconds.'.format(entity.username, timeout))
                return False
            time.sleep(0.3)

        response_text = self._responses[bot_user_id]
        self._delete_response(bot_user_id)
        self._pinged_bots.remove(bot_user_id)

        if isinstance(response_text, str):

            if 'Use /off to pause your subscription.' in response_text \
                    or 'Use /stop to unsubscribe.' in response_text:
                self.botbuilders.append(entity)

            # Evaluate WJClub's ParkMeBot flags
            reserved_username = ZERO_CHAR1 + ZERO_CHAR1 + ZERO_CHAR1 + ZERO_CHAR1
            parked = ZERO_CHAR1 + ZERO_CHAR1 + ZERO_CHAR1 + ZERO_CHAR2
            maintenance = ZERO_CHAR1 + ZERO_CHAR1 + ZERO_CHAR2 + ZERO_CHAR1

            if zero_width_encoding(response_text) in (reserved_username, parked, maintenance):
                return False
        return True

    def get_bot_last_activity(self, entity):
        entity = self.get_bot_entity(entity)

        _, messages, _ = self.client.get_message_history(entity, limit=5)

        peer_messages = [m for m in messages if m.from_id == entity.id]
        if len(peer_messages) == 0:
            return None
        last_peer_message = peer_messages[-1]
        return last_peer_message.date

    def disconnect(self):
        self.client.disconnect()


def check_bot(bot: TelegramBot, bot_checker: BotChecker, to_check: BotModel):
    entity = None

    if to_check.chat_id:
        try:
            entity = bot_checker.get_bot_entity_by_id(to_check.chat_id)
        except Exception as e:
            log.error("Lookup of {bot.username} through its chat_id failed. Trying to retrieve it "
                      "via ResolveUsernameRequest...")

    if entity is None:
        try:
            entity = bot_checker.get_bot_entity(to_check.username)
        except UsernameNotOccupiedError:
            bot.send_message(settings.BOTLIST_NOTIFICATIONS_ID,
                             "{} deleted because the entity does not exist (anymore).".format(
                                 to_check.username))
            to_check.delete_instance()
            return
        time.sleep(2.5)

    # Check basic properties
    to_check.chat_id = int(entity.id)
    to_check.official = bool(entity.verified)
    to_check.inlinequeries = bool(entity.bot_inline_placeholder)
    to_check.username = '@' + str(entity.username)
    if entity in bot_checker.botbuilders:
        to_check.botbuilder = True

    # Check online state
    bot_offline = not bot_checker.ping_bot(entity, timeout=12)

    if to_check.offline != bot_offline:
        to_check.offline = bot_offline

        # We get a lot of false negatives, therefore the bot may set bots online, but only makes
        # a suggestion to set them offline.
        # Suggestion.add_or_update(
        #     UserModel.botlist_user_instance(),
        #     'offline',
        #     to_check,
        #     bot_offline
        # ).save()

        to_check.save()
        bot.send_message(settings.BOTLIST_NOTIFICATIONS_ID, '{} went {}.'.format(
            to_check.str_no_md,
            'online'
        ))

    # Add entry to pings database
    now = datetime.datetime.now()
    ping, created = Ping.get_or_create(bot=to_check, defaults={'last_ping': now})
    ping.last_response = ping.last_response if to_check.offline else now
    ping.save()

    # Download profile picture
    tmp_file = os.path.join(settings.BOT_THUMBNAIL_DIR, '_tmp.jpg')
    photo_file = to_check.thumbnail_file
    sticker_file = os.path.join(settings.BOT_THUMBNAIL_DIR, '_sticker_tmp.webp')

    time.sleep(1)
    downloaded = bot_checker.client.download_profile_photo(entity, tmp_file, download_big=True)

    if downloaded:
        try:
            similar = filecmp.cmp(tmp_file, photo_file, shallow=False)
        except FileNotFoundError:
            similar = False

        if not similar:
            shutil.copy(tmp_file, photo_file)
            if not created:  # if this bot has been pinged before and its pp changed
                make_sticker(photo_file, sticker_file)
                bot.send_message(settings.BOTLIST_NOTIFICATIONS_ID,
                                 "New profile picture of {}:".format(to_check.username),
                                 timeout=360)
                bot.send_sticker(settings.BOTLIST_NOTIFICATIONS_ID,
                                 open(photo_file, 'rb'), timeout=360)

    to_check.save()

    bot_checker.schedule_conversation_deletion(entity, 8)

    # Sleep to give Userbot time to breathe
    time.sleep(4)


@run_async
def job_callback(bot, job):
    bot_checker = job.context.get('checker')
    bot_checker.reset()

    start = datetime.datetime.now()

    total_bot_count = BotModel.select().where(BotModel.userbot == False).count()
    batch_size = 5

    for i in range(1, int(total_bot_count / batch_size) + 1):
        try:
            bots_page = list(
                BotModel.select().where(BotModel.userbot == False).join(
                    Ping, JOIN.LEFT_OUTER).order_by(fn.Random()).paginate(i, batch_size)
            )
            log.info("Checking {}...".format(', '.join(x.username for x in bots_page)))
            for b in bots_page:
                if job.context.get('stop').is_set():
                    raise StopAsyncIteration()
                try:
                    check_bot(bot, bot_checker, b)
                except NotABotError:
                    b.userbot = True
                    b.save()
        except FloodWaitError as e:
            bot.formatter.send_failure(
                settings.ADMINS[0],
                "Userbot received a Flood Wait timeout: {} seconds".format(e.seconds))
            traceback.print_exc()
            log.error("Userbot received a Flood Wait timeout: {} seconds".format(e.seconds))
            return
        except StopAsyncIteration:
            break
        except:
            traceback.print_exc()
            log.debug("Continuing...")
            time.sleep(5)
            continue

    duration = datetime.datetime.now() - start
    bot.send_message(settings.ADMINS[0], "Botchecker completed in {}.".format(duration))


if __name__ == '__main__':
    api_id = 34057
    api_hash = 'a89154bb0cde970cae0848dc7f7a6108'
    phone = '+491728656978'
    # session_file = settings.USERBOT_SESSION  # botchecker
    checker = BotChecker('/home/joscha/accounts/josxa', api_id, api_hash, phone)

    for b in [("@botlistbot", 265482650), ("@gittoolsbot", 403706547), ("@imdb", 141186424)]:
        entity = checker.get_bot_entity_by_id(b[1])
        print(checker.ping_bot(entity))
