# -*- coding: utf-8 -*-
import codecs
import datetime
import logging
import re
import traceback
from time import sleep
from typing import List

import appglobals
import helpers
import mdformat
import settings
import util
from custemoji import Emoji
from dialog import messages
from models import Bot, Country
from models import Category
from models import Notifications
from models import Statistic
from models.channel import Channel
from models.revision import Revision
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import BadRequest, TelegramError
from telegram.ext.dispatcher import run_async
from util import restricted
from logzero import logger as log


def _format_category_bots(category):
    cat_bots = Bot.of_category_without_new(category)
    text = '*' + str(category) + '*\n'
    text += '\n'.join([str(b) for b in cat_bots])
    return text


class BotList:
    FILES_ROOT = appglobals.ROOT_DIR + '/files/'
    NEW_BOTS_FILE = FILES_ROOT + 'new_bots_list.txt'
    CATEGORY_LIST_FILE = FILES_ROOT + 'category_list.txt'
    ENGLISH_INTRO_TEXT = FILES_ROOT + 'intro_en.txt'
    SPANISH_INTRO_TEXT = FILES_ROOT + 'intro_es.txt'

    def __init__(self, bot, update, channel, resend, silent):
        if not channel:
            self.notify_admin_err(
                "I don't know the channel `{}`. Please make sure I am an admin there, "
                "and send a random message so that I can remember the channel meta data.".format(
                    self.channel.username))
            return

        self.bot = bot
        self.update = update
        self.channel = channel
        self.resend = resend
        self.silent = silent
        self.sent = dict()
        self.sent['category'] = list()
        self.chat_id = update.effective_chat.id
        self.message_id = util.mid_from_update(update)

    def notify_admin(self, txt):
        self.bot.formatter.send_or_edit(self.chat_id, Emoji.HOURGLASS_WITH_FLOWING_SAND + ' ' + txt,
                                        to_edit=self.message_id,
                                        disable_web_page_preview=True, disable_notification=False)

    def notify_admin_err(self, txt):
        self.bot.formatter.send_or_edit(self.chat_id, util.failure(txt),
                                        to_edit=self.message_id,
                                        disable_web_page_preview=True, disable_notification=False)

    def _delete_message(self, message_id):
        self.bot.delete_message(self.channel.chat_id, message_id)

    def _save_channel(self):
        self.channel.save()

    @staticmethod
    def create_hyperlink(message_id):
        return 'https://t.me/{}/{}'.format(settings.SELF_CHANNEL_USERNAME, message_id)

    @property
    def portal_markup(self):
        buttons = [
            InlineKeyboardButton("🔺 1️⃣ Categories 📚 🔺",
                                 url=BotList.create_hyperlink(self.channel.category_list_mid)),
            InlineKeyboardButton("▫️ 2️⃣ BotList Bot 🤖 ▫️",
                                 url='https://t.me/botlistbot?start'),
            InlineKeyboardButton("▫️ 3️⃣ BotList Chat 👥💬 ▫️",
                                 url='https://t.me/botlistchat'),
            # InlineKeyboardButton("Add to Group 🤖",
            #                      url='https://t.me/botlistbot?startgroup=start'),
        ]
        return InlineKeyboardMarkup(util.build_menu(buttons, 1))

    @staticmethod
    def _read_file(filename):
        with codecs.open(filename, 'r', 'utf-8') as f:
            return f.read()

    def send_or_edit(self, text, message_id, reply_markup=None):
        sleep(3)
        try:
            if self.resend:
                return util.send_md_message(self.bot, self.channel.chat_id, text, timeout=120,
                                            disable_notification=True, reply_markup=reply_markup)
            else:
                if reply_markup:
                    return self.bot.formatter.send_or_edit(self.channel.chat_id, text,
                                                           to_edit=message_id,
                                                           timeout=120,
                                                           disable_web_page_preview=True,
                                                           disable_notification=True,
                                                           reply_markup=reply_markup)
                else:
                    return self.bot.formatter.send_or_edit(self.channel.chat_id, text,
                                                           to_edit=message_id,
                                                           timeout=120,
                                                           disable_web_page_preview=True,
                                                           disable_notification=True)
        except BadRequest as e:
            if 'chat not found' in e.message.lower():
                self.notify_admin_err(
                    "I can't reach BotList Bot with chat-id `{}` (CHAT NOT FOUND error). "
                    "There's probably something wrong with the database.".format(
                        self.channel.chat_id))
                raise e
            if 'message not modified' in e.message.lower():
                return None
            else:
                log.error(e)
                raise e

    def update_intro(self):
        if self.resend:
            self.notify_admin("Sending intro GIF...")
            self.bot.sendDocument(self.channel.chat_id, open("botlistbot/assets/gif/animation.gif", 'rb'),
                                  timeout=120)
            sleep(1)

        intro_en = self._read_file(self.ENGLISH_INTRO_TEXT)
        intro_es = self._read_file(self.SPANISH_INTRO_TEXT)

        self.notify_admin("Sending english channel intro text...")
        msg_en = self.send_or_edit(intro_en, self.channel.intro_en_mid)
        self.notify_admin("Sending spanish channel intro text...")
        msg_es = self.send_or_edit(intro_es, self.channel.intro_es_mid)

        if msg_en:
            self.sent['intro_en'] = "English intro sent"
            self.channel.intro_en_mid = msg_en.message_id
        if msg_es:
            self.channel.intro_es_mid = msg_es.message_id
            self.sent['intro_es'] = "Spanish intro sent"
        self._save_channel()

    def update_new_bots_list(self):
        text = self._read_file(self.NEW_BOTS_FILE)

        # insert spaces and the name of the bot
        new_bots_joined = Bot.get_new_bots_markdown()
        text = text.format(new_bots_joined)

        msg = self.send_or_edit(text, self.channel.new_bots_mid)
        self.sent['new_bots_list'] = "List of new bots sent"
        if msg:
            self.channel.new_bots_mid = msg.message_id
        self._save_channel()

    def update_category_list(self):
        self.notify_admin('Sending category list...')

        # generate category links to previous messages
        all_categories = '\n'.join(["[{}](https://t.me/{}/{})".format(
            str(c),
            self.channel.username,
            c.current_message_id
        ) for c in Category.select_all()])

        url_stub = 'https://t.me/{}/'.format(self.channel.username)
        category_list = self._read_file(self.CATEGORY_LIST_FILE)

        # Insert placeholders
        text = category_list.format(
            url_stub + str(self.channel.intro_en_mid),
            url_stub + str(self.channel.intro_es_mid),
            all_categories,
            url_stub + str(self.channel.new_bots_mid)
        )

        msg = self.send_or_edit(text, self.channel.category_list_mid)

        if msg:
            self.channel.category_list_mid = msg.message_id
            self.sent['category_list'] = "Category Links sent"
        self._save_channel()

    def update_categories(self, categories: List[Category]):
        self.notify_admin(
            "Updating BotList categories to Revision {}...".format(Revision.get_instance().nr))

        for cat in categories:
            text = _format_category_bots(cat)

            log.info(f"Updating category {cat.name}...")
            msg = self.send_or_edit(text, cat.current_message_id)
            if msg:
                cat.current_message_id = msg.message_id
                self.sent['category'].append("{} {}".format(
                    'Resent' if self.resend else 'Updated',
                    cat
                ))
            cat.save()

        self._save_channel()

        # Add "share", "up", and "down" buttons
        for i in range(0, len(categories)):
            buttons = list()
            if i > 0:
                # Not first category
                # Add "Up" button
                buttons.append(InlineKeyboardButton(
                    "🔺",
                    url=BotList.create_hyperlink(categories[i - 1].current_message_id)))

            buttons.append(
                InlineKeyboardButton("Share", url="https://t.me/{}?start={}".format(
                    settings.SELF_BOT_NAME,
                    categories[i].id)))

            if i < len(categories) - 1:
                # Not last category
                buttons.append(InlineKeyboardButton(
                    "🔻",
                    url=BotList.create_hyperlink(categories[i + 1].current_message_id)))

            reply_markup = InlineKeyboardMarkup([buttons])

            log.info(f"Adding buttons to message with category {categories[i].name}...")
            self.bot.edit_message_reply_markup(
                self.channel.chat_id,
                categories[i].current_message_id,
                reply_markup=reply_markup, timeout=60)

    def send_footer(self):
        num_bots = Bot.select_approved().count()
        self.notify_admin('Sending footer...')

        # add footer as notification
        footer = '\n```'
        footer += '\n' + mdformat.centered(
            "• @BotList •\n{}\n{} bots".format(
                datetime.date.today().strftime("%Y-%m-%d"),
                num_bots
            ))
        footer += '```'

        if self.resend or not self.silent:
            try:
                self._delete_message(self.channel.footer_mid)
            except BadRequest as e:
                pass
            footer_to_edit = None
        else:
            footer_to_edit = self.channel.footer_mid

        footer_msg = self.bot.formatter.send_or_edit(self.channel.chat_id, footer,
                                                     to_edit=footer_to_edit,
                                                     timeout=120,
                                                     disable_notifications=self.silent,
                                                     reply_markup=self.portal_markup)
        if footer_msg:
            self.channel.footer_mid = footer_msg.message_id
            self.sent['footer'] = "Footer sent"
        self._save_channel()

    def finish(self):
        # set last update
        self.channel.last_update = datetime.date.today()
        self._save_channel()

        new_bots = Bot.select_new_bots()
        if not self.silent and len(new_bots) > 0:
            self.notify_admin("Sending notifications to subscribers...")
            subscribers = Notifications.select().where(Notifications.enabled == True)
            notification_count = 0
            for sub in subscribers:
                try:
                    util.send_md_message(self.bot, sub.chat_id,
                                         messages.BOTLIST_UPDATE_NOTIFICATION.format(
                                             n_bots=len(new_bots),
                                             new_bots=Bot.get_new_bots_markdown()))
                    notification_count += 1
                    sub.last_notification = datetime.date.today()
                    sub.save()
                except TelegramError:
                    pass
            self.sent['notifications'] = "Notifications sent to {} users.".format(
                notification_count)

        changes_made = len(self.sent) > 1 or len(self.sent['category']) > 0
        if changes_made:
            text = util.success('{}{}'.format('BotList updated successfully:\n\n',
                                              mdformat.results_list(self.sent)))
        else:
            text = mdformat.none_action("No changes were necessary.")

        log.info(self.sent)
        self.bot.formatter.send_or_edit(self.chat_id, text, to_edit=self.message_id)

    def delete_full_botlist(self):
        all_cats = Category.select_all()
        start = all_cats[0].current_message_id - 3  # Some wiggle room and GIF
        end = all_cats[-1].current_message_id + 4  # Some wiggle room
        self.notify_admin("Deleting all messages...")
        for m in range(start, end):
            try:
                self.bot.delete_message(self.channel.chat_id, m)
            except BadRequest as e:
                pass


@restricted(strict=True)
@run_async
def send_botlist(bot, update, resend=False, silent=False):
    log.info("Re-sending BotList..." if resend else "Updating BotList...")

    channel = helpers.get_channel()
    revision = Revision.get_instance()
    revision.nr += 1
    revision.save()

    all_categories = Category.select_all()

    botlist = BotList(bot, update, channel, resend, silent)
    if resend:
        botlist.delete_full_botlist()
    botlist.update_intro()
    botlist.update_categories(all_categories)
    botlist.update_new_bots_list()
    botlist.update_category_list()
    botlist.send_footer()
    botlist.finish()
    channel.save()
    Statistic.of(update, 'send', 'botlist (resend: {})'.format(str(resend)), Statistic.IMPORTANT)


def new_channel_post(bot, update, photo=None):
    post = update.channel_post
    if post.chat.username != settings.SELF_CHANNEL_USERNAME:
        return
    text = post.text

    channel, created = Channel.get_or_create(chat_id=post.chat_id, username=post.chat.username)
    if created:
        channel.save()

    category_list = '•Share your bots to the @BotListChat using the hashtag #new' in text
    intro = 'Hi! Welcome' in text
    category = text[0] == '•' and not category_list
    new_bots_list = 'NEW→' in text

    # TODO: is this a document?
    if photo:
        pass
    elif category:
        try:
            # get the category meta data
            meta = re.match(r'•(.*?)([A-Z].*):(?:\n(.*):)?', text).groups()
            if len(meta) < 2:
                raise ValueError("Category could not get parsed.")

            emojis = str.strip(meta[0])
            name = str.strip(meta[1])
            extra = str.strip(meta[2]) if meta[2] else None
            try:
                cat = Category.get(name=name)
            except Category.DoesNotExist:
                cat = Category(name=name)
            cat.emojis = emojis
            cat.extra = extra
            cat.save()

            # get the bots in that category
            bots = re.findall(r'^(🆕)?.*(@\w+)( .+)?$', text, re.MULTILINE)
            languages = Country.select().execute()
            for b in bots:
                username = b[1]
                try:
                    new_bot = Bot.by_username(username)
                except Bot.DoesNotExist:
                    new_bot = Bot(username=username)

                new_bot.category = cat

                new_bot.inlinequeries = "🔎" in b[2]
                new_bot.official = "🔹" in b[2]

                extra = re.findall(r'(\[.*\])', b[2])
                if extra:
                    new_bot.extra = extra[0]

                # find language
                for lang in languages:
                    if lang.emoji in b[2]:
                        new_bot.country = lang

                if b[0]:
                    new_bot.date_added = datetime.date.today()
                else:
                    new_bot.date_added = datetime.date.today() - datetime.timedelta(days=31)

                new_bot.save()
        except AttributeError:
            log.error("Error parsing the following text:\n" + text)
