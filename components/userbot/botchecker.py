#!/usr/bin/python3
import datetime
import filecmp
import logging
import os
import shutil
import time
from pprint import pprint
from threading import Thread

from PIL import Image
from telegram import Bot as TelegramBot
from telegram import ForceReply
from telegram.ext import Filters
from telegram.ext import MessageHandler

import settings
from appglobals import db
from model import Bot as BotModel
from telethon import TelegramClient
from telethon.errors import FloodWaitError
from telethon.tl.types import User

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)

client_log = logging.getLogger(TelegramClient.__name__).setLevel(logging.DEBUG)

CONFIRM_PHONE_CODE = "Userbot authorization required. Enter the code you received..."


def extract_updates(update):
    if not hasattr(update, 'updates'):
        return [update]
    else:
        return update.updates


def authorization_handler(bot, update, checker):
    text = update.message.reply_to_message.text
    if text == CONFIRM_PHONE_CODE:
        checker.authorize(update.message.text)


class BotChecker(object):
    def __init__(self, session_name, api_id, api_hash, phone_number, updater=None):
        self.phone_number = phone_number
        self.client = TelegramClient(session_name, api_id, api_hash, update_workers=2)
        self.client.connect()
        self._pinged_bots = []
        self._responses = []

        if not self.client.is_user_authorized():
            log.info("Sending code request...")
            self.client.send_code_request(phone_number)
            if updater:
                updater.bot.send_message(settings.ADMINS[0], CONFIRM_PHONE_CODE, reply_markup=ForceReply())
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

    def authorize(self, code):
        self.client.sign_in(self.phone_number, code)
        self._initialize()

    def _initialize(self):
        self.pending_authorization = False
        self.client.add_update_handler(self._update_handler)

    def _update_handler(self, update):
        try:
            uid = update.message.from_id
        except:
            try:
                uid = update.user_id
            except:
                return
        if uid in self._pinged_bots:
            self._responses.append(uid)

    def _init_thread(self, target, *args, **kwargs):
        thr = Thread(target=target, args=args, kwargs=kwargs)
        thr.start()

    def get_bot_entity(self, username) -> User:
        entity = self.client.get_entity(username)
        if not entity.bot:
            raise AttributeError("This user is not a bot.")
        # pprint(entity.to_dict())
        return entity

    def ping_bot(self, username, timeout=30):
        # TODO: No check yet if the username is really a bot
        entity = self.client.get_input_entity(username)
        bot_user_id = entity.user_id

        # self._init_thread(self._send_message_await_response(entity, '/start'))
        self._pinged_bots.append(bot_user_id)
        self.client.send_message(entity, '/start')

        start = datetime.datetime.now()
        while bot_user_id not in self._responses:
            if datetime.datetime.now() - start > datetime.timedelta(seconds=timeout):
                return False

            time.sleep(0.2)

        self._responses.remove(bot_user_id)
        self._pinged_bots.remove(bot_user_id)
        return True

    def get_last_activity(self, entity):
        entity = self.client.get_entity(entity)
        if not entity.bot:
            raise AttributeError("This user is not a bot.")

        _, messages, _ = self.client.get_message_history(entity, limit=5)

        peer_messages = [m for m in messages if m.from_id == entity.id]
        if len(peer_messages) == 0:
            return None
        last_peer_message = peer_messages[-1]
        return last_peer_message.date

    def disconnect(self):
        self.client.disconnect()


def make_sticker(filename, out_file, max_height=512, transparent=True):
    image = Image.open(filename)

    # resize sticker to match new max height
    # optimize image dimensions for stickers
    if max_height == 512:
        resize_ratio = min(512 / image.width, 512 / image.height)
        image = image.resize((int(image.width * resize_ratio), int(image.height * resize_ratio)))
    else:
        image.thumbnail((512, max_height), Image.ANTIALIAS)

    if transparent:
        canvas = Image.new('RGBA', (512, image.height))
    else:
        canvas = Image.new('RGB', (512, image.height), color='white')

    pos = (0, 0)
    try:
        canvas.paste(image, pos, mask=image)
    except ValueError:
        canvas.paste(image, pos)

    canvas.save(out_file)
    return out_file


def _check_bot(bot: TelegramBot, bot_checker: BotChecker, to_check: BotModel):
    entity = bot_checker.get_bot_entity(to_check.username)

    # Check basic properties
    to_check.official = bool(entity.verified)
    to_check.inlinequeries = bool(entity.bot_inline_placeholder)

    # Check online state
    bot_offline = not bot_checker.ping_bot(to_check.username, timeout=5)
    if to_check.offline != bot_offline:
        to_check.offline = bot_offline
        bot.send_message(settings.BOTLIST_NOTIFICATIONS_ID, '{} went {}.'.format(
            to_check.str_no_md,
            'offline' if bot_offline else 'online'
        ))

    # Download profile picture
    tmp_file = os.path.join(settings.BOT_THUMBNAIL_DIR, '_tmp.jpg')
    photo_file = to_check.thumbnail_file
    sticker_file = os.path.join(settings.BOT_THUMBNAIL_DIR, '_sticker_tmp.webp')

    downloaded = bot_checker.client.download_profile_photo(entity, tmp_file)

    if downloaded:
        try:
            similar = filecmp.cmp(tmp_file, photo_file, shallow=False)
        except FileNotFoundError:
            similar = False

        if not similar:
            shutil.copy(tmp_file, photo_file)
            make_sticker(photo_file, sticker_file)
            bot.send_message(settings.BOTLIST_NOTIFICATIONS_ID, "New profile picture of {}:".format(to_check.username))
            bot.send_sticker(settings.BOTLIST_NOTIFICATIONS_ID, open(photo_file, 'rb'))

    to_check.save()
    time.sleep(2.3)


def job_callback(bot, job):
    bot_checker = job.context

    total_bot_count = BotModel.select().count()
    batch_size = 5

    try:
        for i in range(1, int(total_bot_count / batch_size) + 1):
            bots_page = list(BotModel.select().paginate(i, batch_size))
            log.info("Checking {}...".format(', '.join(x.username for x in bots_page)))
            for b in bots_page:
                _check_bot(bot, bot_checker, b)
    except FloodWaitError as e:
        log.error("Userbot received a Flood Wait timeout: {} minutes".format(int(e.seconds / 60)))


if __name__ == '__main__':
    api_id = 34057
    api_hash = 'a89154bb0cde970cae0848dc7f7a6108'
    phone = '+79639953313'

    checker = BotChecker('hehe', api_id, api_hash, phone)

    print(checker.ping_bot('@josxasandboxbot', timeout=5))
    print(checker.ping_bot('@globaltimezonebot', timeout=5))
    print(checker.ping_bot('@kekbot', timeout=5))
    print(checker.ping_bot('@idletownbot', timeout=5))
