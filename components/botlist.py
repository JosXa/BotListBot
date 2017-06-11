# -*- coding: utf-8 -*-
import codecs
import datetime
import logging
import re
from pprint import pprint
from time import sleep

import const
import helpers
import mdformat
import util
from custemoji import Emoji
from dialog import messages
from model import Bot, Country
from model import Category
from model import Channel
from model import Notifications
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import BadRequest, RetryAfter, TelegramError
from telegram.ext.dispatcher import run_async
from util import restricted

logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.INFO)
log = logging.getLogger(__name__)


@restricted
@run_async
def send_botlist(bot, update, resend=False, silent=False):
    log.info("Re-Sending BotList..." if resend else "Updating BotList...")
    chat_id = util.uid_from_update(update)
    message_id = util.mid_from_update(update)
    channel = helpers.get_channel()
    error = False

    def notify_admin(txt):
        util.send_or_edit_md_message(bot, chat_id, Emoji.HOURGLASS_WITH_FLOWING_SAND + ' ' + txt,
                                     to_edit=message_id,
                                     disable_web_page_preview=True, disable_notification=True)

    def notify_admin_err(txt):
        util.send_or_edit_md_message(bot, chat_id, util.failure(txt),
                                     to_edit=message_id,
                                     disable_web_page_preview=True, disable_notification=True)

    if not channel:
        notify_admin_err(
            "I don't know the channel `{}`. Please make sure I am an admin there, "
            "and send a random message so that I can remember the channel meta data.".format(
                const.SELF_CHANNEL_USERNAME))
        return

    sent = dict()
    sent['category'] = list()

    try:
        if resend:
            notify_admin("Sending intro GIF...")
            bot.sendDocument(channel.chat_id, open("assets/gif/animation.gif", 'rb'), timeout=120)
            sleep(1)

        with codecs.open('files/intro_en.txt', 'r', 'utf-8') as f:
            intro_en = f.read()
        with codecs.open('files/intro_es.txt', 'r', 'utf-8') as f:
            intro_es = f.read()

        notify_admin("Sending english channel intro text...")
        try:
            if resend:
                intro_msg = util.send_md_message(bot, channel.chat_id, intro_en,
                                                 timeout=120, disable_notification=True)
            else:
                intro_msg = util.send_or_edit_md_message(bot, channel.chat_id, intro_en,
                                                         to_edit=channel.intro_en_mid,
                                                         timeout=120,
                                                         disable_web_page_preview=True, disable_notification=True)
            sent['intro_en'] = "English intro sent"
            channel.intro_en_mid = intro_msg.message_id
            sleep(1)
        except BadRequest as e:
            if 'chat not found' in e.message.lower():
                notify_admin_err(
                    "I can't reach BotList Bot with chat-id `{}` (CHAT NOT FOUND error). "
                    "There's probably something wrong with the database.".format(
                        channel.chat_id))
                error = True
                return
            # message not modified
            pass

        notify_admin("Sending spanish channel intro text...")
        try:
            if resend:
                intro_msg = util.send_md_message(bot, channel.chat_id, intro_es,
                                                 timeout=120, disable_notification=True)
            else:
                intro_msg = util.send_or_edit_md_message(bot, channel.chat_id, intro_es,
                                                         to_edit=channel.intro_es_mid,
                                                         timeout=120,
                                                         disable_web_page_preview=True, disable_notification=True)
            sent['intro_es'] = "Spanish intro sent"
            channel.intro_es_mid = intro_msg.message_id
            sleep(1)
        except BadRequest:
            # message not modified
            pass

        counter = 0
        all_categories = Category.select_all()
        n = len(all_categories)
        for cat in all_categories:
            counter += 1
            if counter % 5 == 1:
                notify_admin("Sending/Updating categories *{} to {}* ({} total)...".format(
                    counter, n if counter + 4 > n else counter + 4, n
                ))

            # Bots!
            cat_bots = Bot.of_category(cat)
            text = '*' + str(cat) + '*\n'
            text += '\n'.join([str(b) for b in cat_bots])

            # add "Share" deep-linking button
            buttons = list()
            # if any([b for b in cat_bots if b.description is not None]):
            buttons.append(
                InlineKeyboardButton("Share", url="https://t.me/{}?start={}".format(
                    const.SELF_BOT_NAME, cat.id)))

            # buttons.append(
            #     InlineKeyboardButton("Permalink", callback_data=util.callback_for_action(CallbackActions.PERMALINK,
            #                                                                              {'cid': c.id})))
            # buttons.append(InlineKeyboardButton("Test", url="http://t.me/{}?start={}".format(
            #     const.SELF_CHANNEL_USERNAME, c.current_message_id)))
            reply_markup = InlineKeyboardMarkup([buttons])
            try:
                if resend:
                    msg = util.send_md_message(bot, channel.chat_id, text, reply_markup=reply_markup, timeout=120,
                                               disable_notification=True)
                else:
                    msg = util.send_or_edit_md_message(bot, channel.chat_id, text, reply_markup=reply_markup,
                                                       to_edit=cat.current_message_id, timeout=120,
                                                       disable_web_page_preview=True, disable_notification=True)
                sent['category'].append("Updated {}".format(cat))
                cat.current_message_id = msg.message_id
                cat.save()
            except BadRequest:
                # message not modified
                pass
            sleep(1)

        with codecs.open('files/new_bots_list.txt', 'r', 'utf-8') as f:
            new_bots_text = f.read()

        # build list of newly added bots
        new_bots = Bot.get_new_bots()

        # insert spaces and the name of the bot
        new_bots_joined = Bot.get_new_bots_str()

        new_bots_text = new_bots_text.format(new_bots_joined,
                                             days_new=const.BOT_CONSIDERED_NEW)
        try:
            if resend:
                new_bots_msg = util.send_md_message(bot, channel.chat_id, new_bots_text, timeout=120,
                                                    disable_notification=True)
            else:
                new_bots_msg = util.send_or_edit_md_message(bot, channel.chat_id, new_bots_text,
                                                            to_edit=channel.new_bots_mid,
                                                            timeout=120, disable_web_page_preview=True,
                                                            disable_notification=True)
            sent['new_bots_list'] = "List of new bots sent"
            channel.new_bots_mid = new_bots_msg.message_id
            sleep(1)
        except BadRequest:
            # message not modified
            pass

        # generate category links to previous messages
        categories = '\n'.join(["[{}](https://t.me/{}/{})".format(
            str(c),
            channel.username,
            c.current_message_id
        ) for c in Category.select_all()])
        with codecs.open('files/category_list.txt', 'r', 'utf-8') as f:
            category_list = f.read()

        # insert placeholders in categories list
        category_list = category_list.format(
            "http://t.me/{}/{}".format(channel.username, channel.intro_en_mid),
            "http://t.me/{}/{}".format(channel.username, channel.intro_es_mid),
            categories,
            "http://t.me/{}/{}".format(channel.username, channel.new_bots_mid),
        )
        num_bots = Bot.select().count()

        try:
            if resend:
                category_list_msg = util.send_md_message(bot, channel.chat_id, category_list, timeout=120,
                                                         disable_notification=True)
            else:
                category_list_msg = util.send_or_edit_md_message(bot, channel.chat_id, category_list,
                                                                 to_edit=channel.category_list_mid, timeout=120,
                                                                 disable_web_page_preview=True,
                                                                 disable_notification=True)
            sent['category_list'] = "Category Links sent"
            channel.category_list_mid = category_list_msg.message_id
            sleep(1)
        except BadRequest:
            # message not modified
            pass

        # add footer as notification
        footer = '\n```'
        footer += '\n' + mdformat.centered(
            "• @botlist •\n{}\n{} bots".format(
                datetime.date.today().strftime("%d-%m-%Y"),
                num_bots
            ))
        footer += '```'

        try:
            print('resend: {}'.format(resend))
            print('not silent: {}'.format(not silent))
            if resend or not silent:
                footer_to_edit = None
            else:
                footer_to_edit = channel.footer_mid
            print('footer to edit: {}'.format(footer_to_edit))
            footer_msg = util.send_or_edit_md_message(bot, channel.chat_id, footer,
                                                      to_edit=footer_to_edit,
                                                      timeout=120,
                                                      disable_notifications=silent)
            channel.footer_mid = footer_msg.message_id
        except BadRequest:
            # message not modified
            pass
        sent['footer'] = "Footer sent"

        # set last update
        channel.last_update = datetime.date.today()
        channel.save()

        if not silent and len(new_bots) > 0:
            notify_admin("Sending notifications to subscribers...")
            subscribers = Notifications.select().where(Notifications.enabled == True)
            notification_count = 0
            for sub in subscribers:
                try:
                    util.send_md_message(bot, sub.chat_id, messages.BOTLIST_UPDATE_NOTIFICATION.format(
                        n_bots=len(new_bots),
                        new_bots=new_bots_joined))
                    notification_count += 1
                    sub.last_notification = datetime.date.today()
                    sub.save()
                except TelegramError:
                    pass
            sent['notifications'] = "Notifications sent to {} users.".format(notification_count)

    except RetryAfter as e:
        notify_admin_err(e.message)

    if not error:
        changes_made = len(sent) > 1 or len(sent['category']) > 0
        if changes_made:
            text = util.success('{}{}'.format('Botlist updated successfully:\n\n', mdformat.results_list(sent)))
        else:
            text = mdformat.none_action("No changes were necessary.")

        pprint(sent)

        util.send_or_edit_md_message(bot, chat_id, text, to_edit=message_id)


def new_channel_post(bot, update, photo=None):
    post = update.channel_post
    if post.chat.username != const.SELF_CHANNEL_USERNAME:
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
                    print("New bot created: {}".format(username))
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
