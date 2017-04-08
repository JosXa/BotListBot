# -*- coding: utf-8 -*-
import binascii
import json
import logging
import os
import re
import sys
import time
from pprint import pprint

import datetime
import emoji
from telegram.ext import CallbackQueryHandler
from telegram.ext import Job
from telegram.ext import MessageHandler, \
    Filters, RegexHandler, InlineQueryHandler, ConversationHandler
from telegram.ext import Updater, CommandHandler

import appglobals
import captions
import components.botlist
import const
import helpers
import mdformat
import messages
import search
import util
from components import admin
from components import botlist
from components import botproperties
from components import contributions
from components import eastereggs
from components import favorites
from components import help
from components import inlinequery
from components.botlist import new_channel_post
from const import BotStates, CallbackActions, CallbackStates
from model import Category, Bot, Country
from model import Favorite
from model import Keyword
from model import Notifications
from model.suggestion import Suggestion
from model.user import User
from pwrtelegram import PWRTelegram
from telegram import ForceReply
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram import KeyboardButton
from telegram import ParseMode
from telegram import ReplyKeyboardMarkup
from telegram import ReplyKeyboardRemove
from util import restricted, private_chat_only, track_groups

logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.INFO)
log = logging.getLogger(__name__)


@track_groups
def start(bot, update, args):
    tg_user = update.message.from_user
    chat_id = tg_user.id

    # Get or create the user from/in database
    User.from_telegram_object(tg_user)

    if len(args) > 0:
        # CATEGORY BY ID
        try:
            cat = Category.get(Category.id == args[0])
            return send_category(bot, update, cat)
        except (ValueError, Category.DoesNotExist):
            pass

        query = ' '.join(args).lower()

        # SPECIFIC QUERIES
        if query == const.DeepLinkingActions.CONTRIBUTING:
            return help.contributing(bot, update, quote=False)
        elif query == const.DeepLinkingActions.EXAMPLES:
            return help.examples(bot, update, quote=False)
        elif query == const.DeepLinkingActions.RULES:
            return help.rules(bot, update, quote=False)
        elif query == const.DeepLinkingActions.SEARCH:
            return search_handler(bot, update)

        # SEARCH QUERY
        search_query(bot, update, query)

    else:
        help.help(bot, update)
        util.wait(bot, update)
        if util.is_private_message(update):
            main_menu(bot, update)
        return ConversationHandler.END


def _main_menu_buttons(admin=False):
    buttons = [
        [KeyboardButton(captions.CATEGORIES)],
        [KeyboardButton(captions.NEW_BOTS), KeyboardButton(captions.SEARCH)],
        [KeyboardButton(captions.HELP)],
    ]
    if admin:
        buttons.insert(1, [KeyboardButton(captions.ADMIN_MENU)])
    return buttons


def main_menu(bot, update):
    chat_id = util.cid_from_update(update)
    is_admin = chat_id in const.MODERATORS
    reply_markup = ReplyKeyboardMarkup(_main_menu_buttons(is_admin),
                                       resize_keyboard=True) if util.is_private_message(
        update) else ReplyKeyboardRemove()

    bot.sendMessage(chat_id, mdformat.action_hint("What would you like to do?"),
                    reply_markup=reply_markup)


def manage_subscription(bot, update):
    chat_id = util.cid_from_update(update)
    msg = "Would you like to be notified when new bots arrive at the @BotList?"
    buttons = [[
        InlineKeyboardButton(util.success("Yes"),
                             callback_data=util.callback_for_action(CallbackActions.SET_NOTIFICATIONS,
                                                                    {'value': True})),
        InlineKeyboardButton("No", callback_data=util.callback_for_action(CallbackActions.SET_NOTIFICATIONS,
                                                                          {'value': False}))]]
    reply_markup = InlineKeyboardMarkup(buttons)
    util.send_md_message(bot, chat_id, msg, reply_markup=reply_markup)
    return ConversationHandler.END


def _new_bots_text():
    new_bots = Bot.get_new_bots()
    if len(new_bots) > 0:
        txt = "Fresh new bots from the last {} days 💙:\n\n{}".format(
            const.BOT_CONSIDERED_NEW,
            Bot.get_new_bots_str())
    else:
        txt = 'No new bots available.'
    return txt


# def select_language(bot, update):
#     chat_id = util.cid_from_update(update)
#     msg = util.action_hint("Choose a language")
#     buttons = [[
#         InlineKeyboardButton("🇬🇧 English",
#                              callback_data=util.callback_for_action(CallbackActions.SELECT_LANGUAGE,
#                                                                     {'lang': 'en'})),
#         InlineKeyboardButton("🇪🇸 Spanish", callback_data=util.callback_for_action(CallbackActions.SELECT_LANGUAGE,
#                                                                                     {'lang': 'es'}))]]
#     reply_markup = InlineKeyboardMarkup(buttons)
#     util.send_md_message(bot, chat_id, msg, reply_markup=reply_markup)
#     return ConversationHandler.END


@track_groups
def all_handler(bot, update):
    chat_id = util.cid_from_update(update)
    if update.message and update.message.new_chat_member:
        if update.message.new_chat_member.id == int(
            const.SELF_BOT_ID):
            # bot was added to a group
            start(bot, update)
    return ConversationHandler.END


@restricted
def restart(bot, update):
    chat_id = util.uid_from_update(update)
    # if not admin.check_admin(chat_id):
    #     return
    util.send_message_success(bot, chat_id, "Bot is restarting...")
    time.sleep(0.2)
    os.execl(sys.executable, sys.executable, *sys.argv)


def search_query(bot, update, query, send_errors=True):
    chat_id = util.cid_from_update(update)
    results = search.search_bots(query)
    is_admin = chat_id in const.MODERATORS
    reply_markup = ReplyKeyboardMarkup(_main_menu_buttons(is_admin)) if util.is_private_message(
        update) else ReplyKeyboardRemove()
    if results:
        if len(results) == 1:
            return send_bot_details(bot, update, results[0])
        too_many_results = len(results) > const.MAX_SEARCH_RESULTS

        bots_list = ''
        if chat_id in const.MODERATORS:
            # append edit buttons
            bots_list += '\n'.join(["{} — /edit{} 🛃".format(b, b.id) for b in list(results)[:100]])
        else:
            bots_list += '\n'.join([str(b) for b in list(results)[:const.MAX_SEARCH_RESULTS]])
        bots_list += '\n…' if too_many_results else ''
        bots_list = messages.SEARCH_RESULTS.format(bots=bots_list, num_results=len(results),
                                                   plural='s' if len(results) > 1 else '',
                                                   query=query)
        update.message.reply_text(bots_list, parse_mode=ParseMode.MARKDOWN, reply_markup=reply_markup)
    else:
        if send_errors:
            update.message.reply_text(
                util.failure("Sorry, I couldn't find anything related "
                             "to *{}* in the @BotList. /search".format(util.escape_markdown(query))),
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=reply_markup)
    return ConversationHandler.END


def search_handler(bot, update, args=None):
    if args:
        search_query(bot, update, ' '.join(args))
    else:
        # no search term
        if util.is_group_message(update):
            action = const.DeepLinkingActions.SEARCH
            update.message.reply_text(
                "Please use the search command with arguments or continue in private. "
                "Example: `/search awesome bot`",
                quote=True,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton(
                        captions.SWITCH_PRIVATE,
                        url="https://t.me/{}?start={}".format(
                            const.SELF_BOT_NAME,
                            action)),
                        InlineKeyboardButton('🔎 Search inline', switch_inline_query_current_chat='')
                    ]]
                ))
        else:
            update.message.reply_text(messages.SEARCH_MESSAGE,
                                      reply_markup=ForceReply(selective=True))
    return ConversationHandler.END


def _select_category_buttons(callback_action=None):
    if callback_action is None:
        # set default
        callback_action = CallbackActions.SELECT_BOT_FROM_CATEGORY
    categories = Category.select().order_by(Category.name.asc()).execute()

    buttons = util.build_menu([InlineKeyboardButton(
        '{}{}'.format(emoji.emojize(c.emojis, use_aliases=True), c.name),
        callback_data=util.callback_for_action(
            callback_action, {'id': c.id})) for c in categories], 2)
    buttons.insert(0, [InlineKeyboardButton(
        '🆕 New Bots', callback_data=util.callback_for_action(CallbackActions.NEW_BOTS_SELECTED))])
    return buttons


@track_groups
def select_category(bot, update, callback_action=None):
    chat_id = util.cid_from_update(update)
    util.send_or_edit_md_message(bot, chat_id, util.action_hint(messages.SELECT_CATEGORY),
                                 to_edit=util.mid_from_update(update),
                                 reply_markup=InlineKeyboardMarkup(_select_category_buttons(callback_action)))
    return ConversationHandler.END


def error(bot, update, error):
    log.error(error)


def access_token(bot, update):
    update.message.reply_text(binascii.hexlify(os.urandom(32)).decode('utf-8'))
    return ConversationHandler.END


def credits(bot, update):
    users_contrib = User.select().join()
    pass
    Bot.select(Bot.submitted_by)
    return ConversationHandler.END


def remove_keyboard(bot, update):
    update.message.reply_text("Keyboard removed.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END


@track_groups
def plaintext(bot, update):
    if update.channel_post:
        return new_channel_post(bot, update)

        # if util.is_private_message(update):
        #     if len(update.message.text) > 3:
        #         search_query(bot, update, update.message.text, send_errors=False)


def t3chnostats(bot, update):
    days = 30
    txt = 'Bots approved by other people *in the last {} days*:\n\n'.format(days)
    bots = Bot.select().where(
        (Bot.approved_by != User.get(User.chat_id == 918962)) &
        (Bot.date_added.between(
            datetime.date.today() - datetime.timedelta(days=days),
            datetime.date.today()
        ))
    )
    txt += '\n'.join(['{} by @{}'.format(str(b), b.approved_by.username) for b in bots])
    update.message.reply_text(txt, parse_mode=ParseMode.MARKDOWN)


def show_new_bots(bot, update, back_button=False):
    chat_id = util.cid_from_update(update)
    channel = helpers.get_channel()
    reply_markup = None
    if back_button:
        reply_markup = InlineKeyboardMarkup([[
            InlineKeyboardButton(captions.BACK, callback_data=util.callback_for_action(
                CallbackActions.SELECT_CATEGORY
            )),
            InlineKeyboardButton("Show in BotList",
                                 url="http://t.me/{}/{}".format(channel.username, channel.new_bots_mid)),
            InlineKeyboardButton("Share", switch_inline_query=messages.NEW_BOTS_INLINEQUERY)
        ]])
    util.send_or_edit_md_message(bot, chat_id, _new_bots_text(), to_edit=util.mid_from_update(update),
                                 reply_markup=reply_markup, reply_to_message_id=util.mid_from_update(update))
    return ConversationHandler.END


def send_category(bot, update, category=None):
    chat_id = util.cid_from_update(update)
    bot_list = Bot.of_category(category)[:const.MAX_BOTS_PER_MESSAGE]
    bots_with_description = [b for b in bot_list if b.description is not None]
    detailed_buttons_enabled = len(bots_with_description) > 0 and util.is_private_message(update)

    callback = CallbackActions.SEND_BOT_DETAILS

    if detailed_buttons_enabled:
        buttons = [InlineKeyboardButton(x.username, callback_data=util.callback_for_action(
            callback, {'id': x.id})) for x in bots_with_description]
    else:
        buttons = []
    menu = util.build_menu(buttons, 2)
    menu.insert(0, [
        InlineKeyboardButton(captions.BACK, callback_data=util.callback_for_action(
            CallbackActions.SELECT_CATEGORY
        )),
        InlineKeyboardButton("Show in BotList", url='http://t.me/botlist/{}'.format(category.current_message_id)),
        InlineKeyboardButton("Share", switch_inline_query=category.name)
    ])
    txt = "There are *{}* bots in the category *{}*:\n\n".format(len(bot_list), str(category))

    if chat_id in const.MODERATORS and util.is_private_message(update):
        # append admin edit buttons
        txt += '\n'.join(["{} — /edit{} 🛃".format(b, b.id) for b in bot_list])
    else:
        txt += '\n'.join([str(b) for b in bot_list])

    if detailed_buttons_enabled:
        txt += "\n\n" + util.action_hint("Press a button below to get a detailed description.")
    util.send_or_edit_md_message(bot, chat_id,
                                 txt,
                                 to_edit=util.mid_from_update(update), reply_markup=InlineKeyboardMarkup(menu))


@private_chat_only
def send_bot_details(bot, update, item=None):
    uid = util.uid_from_update(update)
    user = User.from_update(update)
    first_row = list()

    if item is None:
        try:
            text = update.message.text
            bot_in_text = re.findall(const.REGEX_BOT_IN_TEXT, text)[0]
            item = Bot.by_username(bot_in_text)

        # except (AttributeError, Bot.DoesNotExist):
        except Bot.DoesNotExist:
            update.message.reply_text(util.failure(
                "This bot is not in the @BotList. If you think this is a mistake, see the /examples for /contributing."))
            return

    if item.approved:
        # bot is already in the botlist => show information
        txt = item.detail_text
        if item.description is None and not Keyword.select().where(Keyword.entity == item).exists():
            txt += ' is in the @BotList.'
        first_row.insert(0, InlineKeyboardButton(captions.BACK_TO_CATEGORY, callback_data=util.callback_for_action(
            CallbackActions.SELECT_BOT_FROM_CATEGORY, {'id': item.category.id}
        )))
        first_row.append(InlineKeyboardButton(captions.SHARE, switch_inline_query=item.username))

        if uid in const.MODERATORS:
            first_row.append(InlineKeyboardButton(
                "🛃 Edit", callback_data=util.callback_for_action(
                    CallbackActions.EDIT_BOT,
                    {'id': item.id}
                )))
    else:
        txt = '{} is currently pending to be accepted for the @BotList.'.format(item.username)
        if uid in const.MODERATORS:
            first_row.append(InlineKeyboardButton(
                util.success("🛃 Accept"), callback_data=util.callback_for_action(
                    CallbackActions.ACCEPT_BOT,
                    {'id': item.id}
                )))

    buttons = [first_row]
    favs = [f.bot for f in Favorite.select_all(user)]
    if item not in favs:
        buttons.append([
            InlineKeyboardButton(captions.ADD_TO_FAVORITES,
                                 callback_data=util.callback_for_action(CallbackActions.ADD_TO_FAVORITES,
                                                                        {'id': item.id}))
        ])
    reply_markup = InlineKeyboardMarkup(buttons)
    util.send_or_edit_md_message(bot, uid,
                                 txt,
                                 to_edit=util.mid_from_update(update),
                                 reply_markup=reply_markup
                                 )
    return CallbackStates.SHOWING_BOT_DETAILS


def set_notifications(bot, update, value: bool):
    chat_id = util.cid_from_update(update)
    try:
        notifications = Notifications.get(Notifications.chat_id == chat_id)
    except Notifications.DoesNotExist:
        notifications = Notifications(chat_id=chat_id)
    notifications.enabled = value
    notifications.save()

    msg = util.success("Nice! Notifications enabled.") if value else "Ok, notifications disabled."
    msg += '\nYou can always adjust this setting with the /subscribe command.'
    util.send_or_edit_md_message(bot, chat_id, msg, to_edit=util.mid_from_update(update))
    return ConversationHandler.END


def bot_checker_job(bot, job):
    pwt = PWRTelegram('your_token')
    bots = Bot.select()
    for b in bots:
        print('Sending /start to {}...'.format(b.username))
        msg = pwt.send_message(b.username, '/start')
        print('Awaiting response...')
        if msg:
            resp = pwt.await_response(msg)
            if resp:
                print('{} answered.'.format(b.username))
            else:
                print('{} is offline.'.format(b.username))
        else:
            print('Could not contact {}.'.format(b.username))


def cancel(bot, update):
    return ConversationHandler.END


def forward_router(bot, update):
    text = update.message.text
    uid = util.uid_from_update(update)

    # match first username in forwarded message
    try:
        username = re.match(const.REGEX_BOT_IN_TEXT, text).groups()[0]
        if username == '@' + const.SELF_BOT_NAME:
            return  # ignore

        item = Bot.get(Bot.username == username)

        send_bot_details(bot, update, item)

    except (AttributeError, Bot.DoesNotExist):
        pass  # no valid username in forwarded message


def reply_router(bot, update):
    text = update.message.reply_to_message.text

    if text == messages.ADD_FAVORITE:
        query = update.message.text
        favorites.add_favorite_handler(bot, update, query)
    if text == messages.SEARCH_MESSAGE:
        query = update.message.text
        search_query(bot, update, query)
    if text == messages.BAN_MESSAGE:
        query = update.message.text
        admin.ban_handler(bot, update, query, True)
    if text == messages.UNBAN_MESSAGE:
        query = update.message.text
        admin.ban_handler(bot, update, query, False)


def callback_router(bot, update, chat_data):
    obj = json.loads(str(update.callback_query.data))
    user = User.from_update(update)

    if 'a' in obj:
        action = obj['a']

        # HELP
        if action == CallbackActions.HELP:
            help.help(bot, update)
        if action == CallbackActions.CONTRIBUTING:
            help.contributing(bot, update)
        if action == CallbackActions.EXAMPLES:
            help.examples(bot, update)
        # BASIC QUERYING
        if action == CallbackActions.SELECT_CATEGORY:
            select_category(bot, update)
        if action == CallbackActions.SELECT_BOT_FROM_CATEGORY:
            category = Category.get(id=obj['id'])
            send_category(bot, update, category)
        if action == CallbackActions.SEND_BOT_DETAILS:
            item = Bot.get(id=obj['id'])
            send_bot_details(bot, update, item)
        # FAVORITES
        if action == CallbackActions.ADD_FAVORITE:
            favorites.add_favorite_handler(bot, update)
        if action == CallbackActions.REMOVE_FAVORITE_MENU:
            favorites.remove_favorite_menu(bot, update)
        if action == CallbackActions.REMOVE_FAVORITE:
            to_remove = Favorite.get(id=obj['id'])
            to_remove.delete_instance()
            favorites.remove_favorite_menu(bot, update)
        if action == CallbackActions.SEND_FAVORITES_LIST:
            favorites.send_favorites_list(bot, update)
        if action == CallbackActions.ADD_ANYWAY:
            favorites.add_custom(bot, update, obj['u'])
        if action == CallbackActions.ADD_TO_FAVORITES:
            discreet = obj.get('discreet', False)
            item = Bot.get(id=obj['id'])
            favorites.add_favorite(bot, update, item, callback_alert=discreet)
        # ACCEPT/REJECT BOT SUBMISSIONS
        if action == CallbackActions.ACCEPT_BOT:
            to_accept = Bot.get(id=obj['id'])
            admin.edit_bot_category(bot, update, to_accept, CallbackActions.BOT_ACCEPTED)
        if action == CallbackActions.REJECT_BOT:
            to_reject = Bot.get(id=obj['id'])
            notification = obj.get('ntfc', True)
            admin.reject_bot_submission(bot, update, to_reject, verbose=False, notify_submittant=notification)
            admin.approve_bots(bot, update, obj['page'])
        if action == CallbackActions.BOT_ACCEPTED:
            print('CallbackActions.BOT_ACCEPTED')

            to_accept = Bot.get(id=obj['bid'])
            category = Category.get(id=obj['cid'])
            admin.accept_bot_submission(bot, update, to_accept, category)
        # ADD BOT
        # if action == CallbackActions.ADD_BOT_SELECT_CAT:
        #     category = Category.get(id=obj['id'])
        #     admin.add_bot(bot, update, chat_data, category)
        # EDIT BOT
        if action == CallbackActions.EDIT_BOT:
            to_edit = Bot.get(id=obj['id'])
            admin.edit_bot(bot, update, chat_data, to_edit)
        if action == CallbackActions.EDIT_BOT_SELECT_CAT:
            to_edit = Bot.get(id=obj['id'])
            admin.edit_bot_category(bot, update, to_edit)
        if action == CallbackActions.EDIT_BOT_CAT_SELECTED:
            to_edit = Bot.get(id=obj['bid'])
            cat = Category.get(id=obj['cid'])
            botproperties.change_category(bot, update, to_edit, cat)
            admin.edit_bot(bot, update, chat_data, to_edit)
        if action == CallbackActions.EDIT_BOT_COUNTRY:
            to_edit = Bot.get(id=obj['id'])
            botproperties.set_country(bot, update, to_edit)
        if action == CallbackActions.SET_COUNTRY:

            print('CallbackActions.SET_COUNTRY')

            to_edit = Bot.get(id=obj['bid'])
            if obj['cid'] == 'None':
                country = None
            else:
                country = Country.get(id=obj['cid'])
            to_edit.country = country
            to_edit.save()
            admin.edit_bot(bot, update, chat_data, to_edit)
        if action == CallbackActions.EDIT_BOT_DESCRIPTION:
            to_edit = Bot.get(id=obj['id'])
            return botproperties.set_description(bot, update, chat_data, to_edit)
        if action == CallbackActions.EDIT_BOT_EXTRA:
            to_edit = Bot.get(id=obj['id'])
            return botproperties.set_extra(bot, update, chat_data, to_edit)
        if action == CallbackActions.EDIT_BOT_NAME:
            to_edit = Bot.get(id=obj['id'])
            return botproperties.set_name(bot, update, chat_data, to_edit)
        if action == CallbackActions.EDIT_BOT_USERNAME:
            to_edit = Bot.get(id=obj['id'])
            return botproperties.set_username(bot, update, chat_data, to_edit)
        if action == CallbackActions.EDIT_BOT_KEYWORDS:
            to_edit = Bot.get(id=obj['id'])
            return botproperties.set_keywords_init(bot, update, chat_data, to_edit)
        if action == CallbackActions.EDIT_BOT_INLINEQUERIES:
            to_edit = Bot.get(id=obj['id'])
            botproperties.toggle_inlinequeries(bot, update, to_edit)
            admin.edit_bot(bot, update, chat_data, to_edit)
        if action == CallbackActions.EDIT_BOT_OFFICIAL:
            to_edit = Bot.get(id=obj['id'])
            botproperties.toggle_official(bot, update, to_edit)
            admin.edit_bot(bot, update, chat_data, to_edit)
        if action == CallbackActions.EDIT_BOT_OFFLINE:
            to_edit = Bot.get(id=obj['id'])
            botproperties.toggle_offline(bot, update, to_edit)
            admin.edit_bot(bot, update, chat_data, to_edit)
        if action == CallbackActions.EDIT_BOT_SPAM:
            to_edit = Bot.get(id=obj['id'])
            botproperties.toggle_spam(bot, update, to_edit)
            admin.edit_bot(bot, update, chat_data, to_edit)
        if action == CallbackActions.CONFIRM_DELETE_BOT:
            to_delete = Bot.get(id=obj['id'])
            botproperties.delete_bot_confirm(bot, update, to_delete)
        if action == CallbackActions.DELETE_BOT:
            to_edit = Bot.get(id=obj['id'])
            botproperties.delete_bot(bot, update, to_edit)
            send_category(bot, update, to_edit.category)
        if action == CallbackActions.ACCEPT_SUGGESTION:
            suggestion = Suggestion.get(id=obj['id'])
            suggestion.execute()
            admin.approve_suggestions(bot, update, page=obj['page'])
        if action == CallbackActions.REJECT_SUGGESTION:
            suggestion = Suggestion.get(id=obj['id'])
            suggestion.delete_instance()
            admin.approve_suggestions(bot, update, page=obj['page'])
        if action == CallbackActions.SWITCH_SUGGESTIONS_PAGE:
            page = obj['page']
            admin.approve_suggestions(bot, update, page)
        if action == CallbackActions.SWITCH_APPROVALS_PAGE:
            admin.approve_bots(bot, update, page=obj['page'])
        if action == CallbackActions.SET_NOTIFICATIONS:
            set_notifications(bot, update, obj['value'])
        if action == CallbackActions.NEW_BOTS_SELECTED:
            show_new_bots(bot, update, back_button=True)
        if action == CallbackActions.REMOVE_KEYWORD:
            to_edit = Bot.get(id=obj['id'])
            kw = Keyword.get(id=obj['kwid'])
            kw.delete_instance()
            botproperties.set_keywords(bot, update, chat_data, to_edit)
        if action == CallbackActions.ABORT_SETTING_KEYWORDS:
            to_edit = Bot.get(id=obj['id'])
            admin.edit_bot(bot, update, chat_data, to_edit)
        # SEND BOTLIST
        if action == CallbackActions.SEND_BOTLIST:
            silent = obj.get('silent', False)
            re_send = obj.get('re', False)
            components.botlist.send_botlist(bot, update, resend=re_send, silent=silent)
        if action == CallbackActions.RESEND_BOTLIST:
            components.botlist.send_botlist(bot, update, resend=True)

        return ConversationHandler.END


def main():
    # TODO: start api

    try:
        BOT_TOKEN = str(os.environ['TG_TOKEN'])
    except Exception:
        BOT_TOKEN = str(sys.argv[1])

    updater = Updater(BOT_TOKEN, workers=2)

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    conv_handler = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(callback_router, pass_chat_data=True),
            CommandHandler('category', select_category),
            CommandHandler('search', search_handler, pass_args=True),
            CommandHandler('s', search_handler, pass_args=True),
            CommandHandler('cat', select_category),
            # CallbackQueryHandler(callback_router, pass_chat_data=True)
        ],
        states={
            BotStates.SENDING_DESCRIPTION: [
                MessageHandler(Filters.text, botproperties.set_description, pass_chat_data=True)
            ],
            BotStates.SENDING_EXTRA: [
                MessageHandler(Filters.text, botproperties.set_extra, pass_chat_data=True)
            ],
            BotStates.SENDING_NAME: [
                MessageHandler(Filters.text, botproperties.set_name, pass_chat_data=True)
            ],
            BotStates.SENDING_USERNAME: [
                MessageHandler(Filters.text, botproperties.set_username, pass_chat_data=True)
            ],
            BotStates.SENDING_KEYWORDS: [
                MessageHandler(Filters.text, botproperties.add_keyword, pass_chat_data=True)
            ],
            # BotStates.SEARCHING: [
            #     MessageHandler(Filters.text, search_handler)
            # ],
        },
        fallbacks=[
            CallbackQueryHandler(callback_router, pass_chat_data=True),
            CommandHandler('start', start, pass_args=True),
            CommandHandler("cancel", cancel)
        ],
    )
    conv_handler.allow_reentry = True
    dp.add_handler(conv_handler)

    dp.add_handler(MessageHandler(Filters.reply, reply_router))
    dp.add_handler(MessageHandler(Filters.forwarded, forward_router))

    dp.add_handler(CommandHandler('start', start, pass_args=True))
    dp.add_handler(CommandHandler("admin", admin.menu))
    dp.add_handler(CommandHandler("a", admin.menu))
    dp.add_handler(CommandHandler("promo", botlist.preview_promo_message))

    # admin menu
    dp.add_handler(RegexHandler(captions.EXIT, main_menu))
    dp.add_handler(RegexHandler(captions.APPROVE_BOTS + '.*', admin.approve_bots))
    dp.add_handler(RegexHandler(captions.APPROVE_SUGGESTIONS + '.*', admin.approve_suggestions))
    dp.add_handler(RegexHandler(captions.SEND_BOTLIST, admin.prepare_transmission, pass_chat_data=True))
    dp.add_handler(RegexHandler(captions.SEND_CONFIG_FILES, admin.send_config_files))
    dp.add_handler(RegexHandler(captions.FIND_OFFLINE, admin.send_offline))

    # main menu
    dp.add_handler(RegexHandler(captions.ADMIN_MENU, admin.menu))
    dp.add_handler(RegexHandler(captions.CATEGORIES, select_category))
    dp.add_handler(RegexHandler(captions.NEW_BOTS, show_new_bots))
    dp.add_handler(RegexHandler(captions.SEARCH, search_handler))
    dp.add_handler(RegexHandler(captions.CONTRIBUTING, help.contributing))
    dp.add_handler(RegexHandler(captions.EXAMPLES, help.examples))
    dp.add_handler(RegexHandler(captions.HELP, help.help))

    dp.add_handler(RegexHandler("^/edit\d+$", admin.edit_bot, pass_chat_data=True))
    dp.add_handler(CommandHandler('reject', admin.reject_bot_submission))
    dp.add_handler(CommandHandler('rej', admin.reject_bot_submission))

    dp.add_handler(CommandHandler('new', contributions.new_bot_submission, pass_args=True))
    dp.add_handler(RegexHandler('.*#new.*', contributions.new_bot_submission))
    dp.add_handler(CommandHandler('offline', contributions.notify_bot_offline, pass_args=True))
    dp.add_handler(RegexHandler('.*#offline.*', contributions.notify_bot_offline))
    dp.add_handler(CommandHandler('spam', contributions.notify_bot_spam, pass_args=True))
    dp.add_handler(RegexHandler('.*#spam.*', contributions.notify_bot_spam))
    dp.add_handler(RegexHandler('^{}$'.format(const.REGEX_BOT_ONLY), send_bot_details))

    dp.add_handler(CommandHandler('r', restart))
    dp.add_handler(CommandHandler('help', help.help))
    dp.add_handler(CommandHandler("contributing", help.contributing))
    dp.add_handler(CommandHandler("contribute", help.contributing))
    dp.add_handler(CommandHandler("examples", help.examples))
    dp.add_handler(CommandHandler("rules", help.rules))

    dp.add_handler(CommandHandler("addfavorite", favorites.send_favorites_list))
    dp.add_handler(CommandHandler("addfav", favorites.add_favorite_handler, pass_args=True))
    dp.add_handler(CommandHandler("f", favorites.send_favorites_list))
    dp.add_handler(CommandHandler("fav", favorites.send_favorites_list))
    dp.add_handler(CommandHandler("favorites", favorites.send_favorites_list))

    dp.add_handler(CommandHandler('ban', lambda bot, update, args: admin.ban_handler(
        bot, update, args, True), pass_args=True))
    dp.add_handler(CommandHandler('unban', lambda bot, update, args: admin.ban_handler(
        bot, update, args, False), pass_args=True))
    dp.add_handler(CommandHandler('t3chno', t3chnostats))
    dp.add_handler(CommandHandler('random', eastereggs.send_random_bot))
    dp.add_handler(CommandHandler('easteregg', eastereggs.send_next, pass_args=True))

    dp.add_handler(CommandHandler("removekeyboard", remove_keyboard))

    dp.add_handler(CommandHandler("subscribe", manage_subscription))
    dp.add_handler(CommandHandler("newbots", show_new_bots))

    dp.add_handler(CommandHandler("accesstoken", access_token))

    dp.add_handler(InlineQueryHandler(inlinequery.inlinequery_handler))
    dp.add_error_handler(error)
    dp.add_handler(MessageHandler(Filters.text, plaintext, allow_edited=True))
    dp.add_handler(MessageHandler(Filters.all, all_handler))

    # users = User.select().join(
    #     Bot.select(
    #         Bot.submitted_by, fn.COUNT(Bot.submitted_by).alias('num_submissions')
    #     ), on=(Bot.submitted_by == )
    # )
    # users = User.select().join(
    #     Bot.select(
    #         Bot.submitted_by, fn.COUNT(Bot.submitted_by).alias('num_submissions')
    #     ).group_by(Bot.submitted_by), on=Bot.submitted_by
    # )
    # pprint(users)


    # JOBS
    # TIME = 60 * 60
    # updater.job_queue.put(Job(channel_checker_job, TIME), next_t=0)
    updater.job_queue.put(Job(admin.last_update_job, 60 * 60 * 10), next_t=60 * 60)  # 60*60

    updater.start_polling()

    log.info('Listening...')
    updater.idle()
    log.info('Disconnecting...')
    appglobals.disconnect()


if __name__ == '__main__':
    main()
