from random import random

import logging
from telegram.ext import JobQueue, Job, run_async
from typing import *
import re

import maya
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ParseMode, Message, Bot

import captions
import settings
import util
from custom_botlistbot import BotListBot
from dialog import messages
from settings import SELF_CHANNEL_USERNAME

from logzero import logger as log


def slang_datetime(dt) -> str:
    maya_date = maya.MayaDT(dt.timestamp())
    return maya_date.slang_time()


def find_bots_in_text(text: str, first=False):
    matches = re.findall(settings.REGEX_BOT_ONLY, text)
    if not matches:
        return None

    try:
        return matches[0] if first else matches
    except:
        return None


def format_name(entity):
    res = entity.first_name or ""
    if entity.first_name and entity.last_name:
        res += " " + entity.last_name
    elif entity.last_name:
        res = entity.last_name
    return res


def validate_username(username: str):
    if len(username) < 3:
        return False
    if username[0] != "@":
        username = "@" + username
    match = re.match(settings.REGEX_BOT_ONLY, username)
    return username if match else False


def get_commands():
    commands = ""
    try:
        with open("files/commands.txt", "rb") as file:
            for command in file.readlines():
                commands += "/" + command.decode("utf-8")
        return commands
    except FileNotFoundError:
        log.error("File could not be opened.")


def get_channel():
    from models import Channel

    try:
        return Channel.get(Channel.username == SELF_CHANNEL_USERNAME)
    except Channel.DoesNotExist:
        return False


def botlist_url_for_category(category):
    return "http://t.me/{}/{}".format(
        get_channel().username, category.current_message_id
    )


def format_keyword(kw):
    kw = kw[1:] if kw[0] == "#" else kw
    kw = kw.replace(" ", "_")
    kw = kw.replace("-", "_")
    kw = kw.replace("'", "_")
    kw = kw.lower()
    return kw


def reroute_private_chat(
    bot, update, quote, action, message, redirect_message=None, reply_markup=None
):
    cid = update.effective_chat.id
    mid = util.mid_from_update(update)
    if redirect_message is None:
        redirect_message = messages.REROUTE_PRIVATE_CHAT

    if util.is_group_message(update):
        update.message.reply_text(
            redirect_message,
            quote=quote,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            captions.SWITCH_PRIVATE,
                            url="https://t.me/{}?start={}".format(
                                settings.SELF_BOT_NAME, action
                            ),
                        ),
                        InlineKeyboardButton(
                            "🔎 Switch to inline", switch_inline_query=action
                        ),
                    ]
                ]
            ),
        )
    else:
        if mid:
            bot.formatter.send_or_edit(cid, message, mid, reply_markup=reply_markup)
        else:
            update.message.reply_text(
                message,
                quote=quote,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=reply_markup,
            )


def make_sticker(filename, out_file, max_height=512, transparent=True):
    return  # TODO: fix
    from PIL import Image

    image = Image.open(filename)

    # resize sticker to match new max height
    # optimize image dimensions for stickers
    if max_height == 512:
        resize_ratio = min(512 / image.width, 512 / image.height)
        image = image.resize(
            (int(image.width * resize_ratio), int(image.height * resize_ratio))
        )
    else:
        image.thumbnail((512, max_height), Image.ANTIALIAS)

    if transparent:
        canvas = Image.new("RGBA", (512, image.height))
    else:
        canvas = Image.new("RGB", (512, image.height), color="white")

    pos = (0, 0)
    try:
        canvas.paste(image, pos, mask=image)
    except ValueError:
        canvas.paste(image, pos)

    canvas.save(out_file)
    return out_file


@run_async
def try_delete_after(
    job_queue: JobQueue,
    messages: Union[List[Union[Message, int]], Union[Message, int]],
    delay: Union[float, int],
):
    if isinstance(messages, (Message, int)):
        _messages = [messages]
    else:
        _messages = messages

    @run_async
    def delete_messages(*args, **kwargs):
        # noinspection PyTypeChecker
        bot: BotListBot = job_queue.bot
        for m in _messages:
            bot.delete_message(m.chat_id, m.message_id, timeout=10, safe=True)

    job_queue.run_once(delete_messages, delay, name="try_delete_after")

