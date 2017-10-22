# -*- coding: utf-8 -*-

import datetime

import captions
import const
import helpers
import mdformat
import settings
import util
from components import admin
from const import BotStates, CallbackActions
from custemoji import Emoji
from dialog import messages
from model import Country
from model import Keyword
from model import Statistic
from model import Suggestion
from model import User
from telegram import ForceReply, InlineKeyboardButton, InlineKeyboardMarkup
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram import ParseMode
from telegram.ext import ConversationHandler

from model import track_activity
from util import restricted

CLEAR_QUERY = "x"


def _is_clear_query(query):
    return query.lower() == CLEAR_QUERY


@restricted
def set_country_menu(bot, update, to_edit):
    uid = util.uid_from_update(update)
    countries = Country.select().order_by(Country.name).execute()

    buttons = util.build_menu(
        [InlineKeyboardButton(
            '{} {}'.format(c.emojized, c.name),
            callback_data=util.callback_for_action(
                CallbackActions.SET_COUNTRY, {'cid': c.id, 'bid': to_edit.id})) for c in countries
         ], 3)
    buttons.insert(0, [
        InlineKeyboardButton(captions.BACK,
                             callback_data=util.callback_for_action(CallbackActions.EDIT_BOT,
                                                                    {'id': to_edit.id})),
        InlineKeyboardButton("None",
                             callback_data=util.callback_for_action(CallbackActions.SET_COUNTRY,
                                                                    {'cid': 'None', 'bid': to_edit.id})),
    ])
    return bot.formatter.send_or_edit(uid, util.action_hint(
        "Please select a country/language for {}".format(to_edit)),
                                        to_edit=util.mid_from_update(update),
                                        reply_markup=InlineKeyboardMarkup(buttons))


def set_country(bot, update, to_edit, country):
    user = User.from_update(update)

    if check_suggestion_limit(bot, update, user):
        return
    if isinstance(country, Country):
        value = country.id
    elif country is None or country == 'None':
        value = None
    else:
        raise AttributeError("Error setting country to {}.".format(country))
    sugg = Suggestion.add_or_update(user, 'country', to_edit, value)


def set_text_property(bot, update, chat_data, property_name, to_edit=None):
    uid = util.uid_from_update(update)
    user = User.from_update(update)
    if check_suggestion_limit(bot, update, user):
        return

    if to_edit:
        text = (
            util.escape_markdown(getattr(to_edit, property_name)) + "\n\n" if getattr(to_edit, property_name) else '')
        text += mdformat.action_hint(
            messages.SET_BOTPROPERTY.format(
                property_name,
                util.escape_markdown(to_edit.username),
                CLEAR_QUERY
            ))
        if property_name == 'description':
            text += ', markdown enabled.'
        update.effective_message.reply_text(text, reply_markup=ForceReply(selective=True),
                                            parse_mode=ParseMode.MARKDOWN)
        chat_data['edit_bot'] = to_edit
    elif update.message:
        value = None
        text = update.message.text

        to_edit = chat_data.get('edit_bot', None)

        def too_long(n):
            bot.formatter.send_failure(uid, "Your {} text is too long, it must be shorter "
                                                "than {} characters. Please try again.".format(property_name, n))
            util.wait(bot, update)
            return admin.edit_bot(bot, update, chat_data, to_edit)

        # Validation
        if property_name == 'description' and len(text) > 300:
            return too_long(300)
        if property_name == 'username':
            value = helpers.validate_username(text)
            if value:
                to_edit = chat_data.get('edit_bot', None)
            else:
                bot.formatter.send_failure(uid, "The username you entered is not valid. Please try again...")
                return admin.edit_bot(bot, update, chat_data, to_edit)

        if not value:
            value = text

        if to_edit:
            if _is_clear_query(text):
                Suggestion.add_or_update(user, property_name, to_edit, None)
            else:
                Suggestion.add_or_update(user, property_name, to_edit, value)
            admin.edit_bot(bot, update, chat_data, to_edit)
        else:
            bot.formatter.send_failure(uid, "An unexpected error occured.")


@restricted
def toggle_value(bot, update, property_name, to_edit, value):
    user = User.from_update(update)

    if check_suggestion_limit(bot, update, user):
        return
    Suggestion.add_or_update(user, property_name, to_edit, bool(value))


@restricted
def set_keywords_init(bot, update, chat_data, context):
    to_edit = context.get('to_edit')
    chat_data['set_keywords_msg'] = util.mid_from_update(update)
    return set_keywords(bot, update, chat_data, to_edit)


@restricted
@track_activity('menu', 'set keywords', Statistic.DETAILED)
def set_keywords(bot, update, chat_data, to_edit):
    chat_id = util.uid_from_update(update)
    keywords = Keyword.select().where(Keyword.entity == to_edit)
    chat_data['edit_bot'] = to_edit
    set_keywords_msgid = chat_data.get('set_keywords_msg')

    kw_remove_buttons = [InlineKeyboardButton('{} ✖️'.format(x),
                                              callback_data=util.callback_for_action(CallbackActions.REMOVE_KEYWORD,
                                                                                     {'id': to_edit.id, 'kwid': x.id}))
                         for x in keywords]
    buttons = util.build_menu(kw_remove_buttons, 2, header_buttons=[
        InlineKeyboardButton(captions.DONE,
                             callback_data=util.callback_for_action(CallbackActions.ABORT_SETTING_KEYWORDS,
                                                                    {'id': to_edit.id}))
    ])
    reply_markup = InlineKeyboardMarkup(buttons)
    msg = util.send_or_edit_md_message(bot,
                                       chat_id,
                                       util.action_hint('Send me the keywords for {} one by one...\n\n{}'.format(
                                           util.escape_markdown(to_edit.username), messages.KEYWORD_BEST_PRACTICES)),
                                       to_edit=set_keywords_msgid,
                                       reply_markup=reply_markup)
    chat_data['set_keywords_msg'] = msg.message_id
    return BotStates.SENDING_KEYWORDS


@restricted
def add_keyword(bot, update, chat_data):
    kw = update.message.text
    bot_to_edit = chat_data.get('edit_bot')
    kw = helpers.format_keyword(kw)
    if len(kw) <= 1:
        update.message.reply_text('Keywords must be longer than 1 character.')
        return
    if len(kw) >= 20:
        update.message.reply_text('Keywords must not be longer than 20 characters.')

    # ignore duplicates
    try:
        Keyword.get((Keyword.name == kw) & (Keyword.entity == bot_to_edit))
        return
    except Keyword.DoesNotExist:
        pass
    kw_obj = Keyword(name=kw, entity=bot_to_edit)
    kw_obj.save()
    set_keywords(bot, update, chat_data, bot_to_edit)
    Statistic.of(update, 'added keyword to'.format(kw), bot_to_edit.username)


@restricted
def delete_bot_confirm(bot, update, to_edit):
    chat_id = util.uid_from_update(update)
    reply_markup = InlineKeyboardMarkup([[
        InlineKeyboardButton("Yes, delete it!", callback_data=util.callback_for_action(
            CallbackActions.DELETE_BOT, {'id': to_edit.id}
        )),
        InlineKeyboardButton(captions.BACK, callback_data=util.callback_for_action(
            CallbackActions.EDIT_BOT, {'id': to_edit.id}
        ))
    ]]
    )
    bot.formatter.send_or_edit(chat_id, "Are you sure?", to_edit=util.mid_from_update(update),
                                 reply_markup=reply_markup)


@restricted
def delete_bot(bot, update, to_edit):
    chat_id = util.uid_from_update(update)
    username = to_edit.username
    to_edit.delete_instance()
    bot.formatter.send_or_edit(chat_id, "Bot has been deleted.", to_edit=util.mid_from_update(update))
    Statistic.of(update, 'delete', username, Statistic.IMPORTANT)


@restricted
def change_category(bot, update, to_edit, category):
    uid = update.effective_user.id
    user = User.get(User.chat_id == uid)
    if uid in settings.MODERATORS and not uid == 918962:
        if check_suggestion_limit(bot, update, user):
            return
        Suggestion.add_or_update(user, 'category', to_edit, category.id)
    else:
        to_edit.category = category
        to_edit.save()


def check_suggestion_limit(bot, update, user):
    cid = update.effective_chat.id
    if Suggestion.over_limit(user):
        bot.formatter.send_failure(cid,
                                  "You have reached the limit of {} suggestions. Please wait for "
                                  "the Moderators to approve of some of them.".format(settings.SUGGESTION_LIMIT))
        Statistic.of(update, 'hit the suggestion limit')
        return True
    return False


def change_suggestion(bot, update, suggestion, page_handover):
    cid = update.effective_chat.id
    mid = update.effective_message.message_id

    text = '{}:\n\n{}'.format(str(suggestion), suggestion.value)
    if suggestion.action == 'description':
        callback_action = CallbackActions.EDIT_BOT_DESCRIPTION
    elif suggestion.action == 'extra':
        callback_action = CallbackActions.EDIT_BOT_EXTRA
    elif suggestion.action == 'name':
        callback_action = CallbackActions.EDIT_BOT_NAME
    elif suggestion.action == 'username':
        callback_action = CallbackActions.EDIT_BOT_USERNAME
    else:
        return  # should not happen

    buttons = [[
        InlineKeyboardButton(captions.BACK,
                             callback_data=util.callback_for_action(CallbackActions.SWITCH_SUGGESTIONS_PAGE,
                                                                    {'page': page_handover}))
    ], [
        InlineKeyboardButton("{} Accept".format(Emoji.WHITE_HEAVY_CHECK_MARK), callback_data=util.callback_for_action(
            CallbackActions.ACCEPT_SUGGESTION, {'id': suggestion.id, 'page': page_handover}
        )),
        InlineKeyboardButton(captions.CHANGE_SUGGESTION, callback_data=util.callback_for_action(
            callback_action, {'id': suggestion.id, 'page': page_handover}
        ))
    ]]

    reply_markup = InlineKeyboardMarkup(buttons)
    bot.formatter.send_or_edit(cid, text, to_edit=mid, disable_web_page_preview=True, reply_markup=reply_markup)


def remove_keyword(bot, update, chat_data, context):
    to_edit = context.get('to_edit')
    kw = context.get('keyword')
    kw.delete_instance()
    return set_keywords(bot, update, chat_data, to_edit)


@restricted
def accept_suggestion(bot, update, suggestion):
    suggestion.apply()
    if suggestion.action == 'offline':
        bot.send_message(settings.BOTLIST_NOTIFICATIONS_ID, '{} went {}.'.format(
            suggestion.subject.str_no_md,
            'offline' if suggestion.subject.offline else 'online'
        ))