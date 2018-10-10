# -*- coding: utf-8 -*-

import helpers
import mdformat
import settings
import util
from actions import *
from components import admin
from const import BotStates, CallbackActions
from dialog import messages
from flow.actionbutton import ActionButton
from flow.context import FlowContext
from models import Bot, Country, Keyword, Statistic, Suggestion, User, track_activity
from telegram import ForceReply, InlineKeyboardMarkup, ParseMode, Update
from telegram.error import BadRequest
from util import restricted

CLEAR_QUERY = "x"


def _is_clear_query(query):
    return query.lower() == CLEAR_QUERY


def set_country_menu(update: Update, context: FlowContext[BotViewModel]):
    uid = update.effective_user.id
    countries = Country.select().order_by(Country.name).execute()
    to_edit = context.view_model.bot

    buttons = util.build_menu(
        [
            ActionButton(Actions.SET_COUNTRY,
                         '{} {}'.format(c.emojized, c.name),
                         BotCategoryModel(category=c, bot=to_edit))
            for c in countries
        ], 3)

    buttons.insert(0, [
        ActionButton(captions.BACK, Actions.EDIT_BOT, BotViewModel(to_edit)),
        ActionButton(Actions.SET_COUNTRY, "None", BotCategoryModel(category=None, bot=to_edit))
    ])
    return context.bot.send_or_edit(uid, util.action_hint(
        "Please select a country/language for {}".format(to_edit)),
                                              to_edit=update.effective_message.message_id,
                                              reply_markup=InlineKeyboardMarkup(buttons))


def set_country(update: Update, context: FlowContext, to_edit, country):
    user = User.from_update(update)

    if check_suggestion_limit(update, context, user):
        return
    if isinstance(country, Country):
        value = country.id
    elif country is None or country == 'None':
        value = None
    else:
        raise AttributeError("Error setting country to {}.".format(country))
    Suggestion.add_or_update(user, 'country', to_edit, value)


def set_text_property(update: Update, context: FlowContext, property_name, to_edit=None):
    uid = update.effective_user.id
    user = User.from_update(update)
    if check_suggestion_limit(update, context, user):
        return

    if to_edit:
        text = (
            util.escape_markdown(getattr(to_edit, property_name)) + "\n\n" if getattr(to_edit,
                                                                                      property_name) else '')
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
        context.chat_data['edit_bot'] = to_edit
    elif update.message:
        value = None
        text = update.message.text

        to_edit = context.chat_data.get('edit_bot', None)

        def too_long(n):
            context.bot.send_failure(uid, "Your {} text is too long, it must be shorter "
                                                    "than {} characters. Please try again.".format(
                property_name, n))
            util.wait(update, context)
            return admin.edit_bot(update, context, to_edit)

        # Validation
        if property_name == 'description' and len(text) > 300:
            return too_long(300)
        if property_name == 'username':
            value = helpers.validate_username(text)
            if value:
                to_edit = context.chat_data.get('edit_bot', None)
            else:
                context.bot.send_failure(uid,
                                                   "The username you entered is not valid. Please try again...")
                return admin.edit_bot(update, context, to_edit)

        if not value:
            value = text

        if to_edit:
            if _is_clear_query(text):
                Suggestion.add_or_update(user, property_name, to_edit, None)
            else:
                Suggestion.add_or_update(user, property_name, to_edit, value)
            admin.edit_bot(update, context, to_edit)
        else:
            context.bot.send_failure(uid, "An unexpected error occured.")


def toggle_value(update: Update, context: FlowContext, property_name, to_edit, value):
    user = User.from_update(update)

    if check_suggestion_limit(update, context, user):
        return
    Suggestion.add_or_update(user, property_name, to_edit, bool(value))


def set_keywords_init(update: Update, context: FlowContext, values):
    to_edit = values.get('to_edit')
    context.chat_data['set_keywords_msg'] = update.effective_message.message_id
    return RerouteToAction(Actions.SET_KEYWORDS, BotViewModel(to_edit))


@track_activity('menu', 'set keywords', Statistic.DETAILED)
def set_keywords(update: Update, context: FlowContext[BotViewModel]):
    to_edit = context.view_model.bot
    chat_id = update.effective_user.id
    keywords = Keyword.select().where(Keyword.entity == to_edit)
    context.chat_data['edit_bot'] = to_edit
    set_keywords_msgid = context.chat_data.get('set_keywords_msg')

    pending = Suggestion.select().where(
        Suggestion.executed == False,
        Suggestion.subject == to_edit,
        Suggestion.action << ['add_keyword', 'remove_keyword']
    )
    pending_removal = [y for y in pending if y.action == 'remove_keyword']

    # Filter keywords by name to not include removal suggestions
    # We don't need to do this for add_keyword suggestions, because duplicates are not allowed.
    keywords = [k for k in keywords if k.name not in [s.value for s in pending_removal]]

    kw_remove_buttons = [
        ActionButton(Actions.REMOVE_KEYWORD,
                     '{} ✖️'.format(x),
                     BotKeywordModel(bot=to_edit, keyword=x))
        for x in keywords]

    kw_remove_buttons.extend([
        ActionButton(Actions.DELETE_KEYWORD_SUGGESTION,
                     '#{} 👓✖️'.format(x.value),
                     SuggestionModel(bot_to_edit=to_edit, suggestion=x))
        for x in [y for y in pending if y.action == 'add_keyword']])

    kw_remove_buttons.extend([
        ActionButton(Actions.DELETE_KEYWORD_SUGGESTION,
                     '#{} 👓✖️'.format(x.value),
                     SuggestionModel(bot_to_edit=to_edit, suggestion=x))
        for x in pending_removal])

    buttons = util.build_menu(kw_remove_buttons, 2, header_buttons=[
        ActionButton(captions.DONE,
                     Actions.ABORT_SETTING_KEYWORDS,
                     BotViewModel(bot=to_edit))
    ])

    reply_markup = InlineKeyboardMarkup(buttons)
    msg = context.bot.send_or_edit(
        chat_id,
        util.action_hint('Send me the keywords for {} one by one...\n\n{}'.format(
            util.escape_markdown(to_edit.username), messages.KEYWORD_BEST_PRACTICES)),
        message_id=set_keywords_msgid,
        reply_markup=reply_markup)

    if msg:
        # message might not have been edited if the user adds an already-existing keyword
        # TODO: should the user be notified about this?
        context.chat_data['set_keywords_msg'] = msg.message_id

    return BotStates.SENDING_KEYWORDS


def add_keyword(update: Update, context: FlowContext):
    user = User.from_telegram_object(update.effective_user)
    if check_suggestion_limit(update, context, user):
        return
    kw = update.message.text
    bot_to_edit = context.chat_data.get('edit_bot')
    kw = helpers.format_keyword(kw)

    # Sanity checks
    if kw in settings.FORBIDDEN_KEYWORDS:
        update.message.reply_text('The keyword {} is forbidden.'.format(kw))
        return
    if len(kw) <= 1:
        update.message.reply_text('Keywords must be longer than 1 character.')
        return
    if len(kw) >= 20:
        update.message.reply_text('Keywords must not be longer than 20 characters.')

    # Ignore duplicates
    try:
        Keyword.get((Keyword.name == kw) & (Keyword.entity == bot_to_edit))
        return
    except Keyword.DoesNotExist:
        pass

    Suggestion.add_or_update(user=user, action='add_keyword', subject=bot_to_edit, value=kw)
    Statistic.of(update, 'added keyword to'.format(kw), bot_to_edit.username)
    return RerouteToAction(Actions.SET_KEYWORDS, BotViewModel(bot_to_edit))


def delete_keyword_suggestion(update: Update, context: FlowContext, values):
    suggestion = values.get('suggestion')
    suggestion.delete_instance()
    return RerouteToAction(Actions.SET_KEYWORDS, BotViewModel(values.get('to_edit')))


@restricted
def delete_bot_confirm(bot, update, to_edit):
    chat_id = update.effective_user.id
    markup = InlineKeyboardMarkup([[
        ActionButton(Actions.DELETE_BOT, BotViewModel(to_edit)),
        ActionButton(captions.BACK, Actions.EDIT_BOT, BotViewModel(to_edit))
    ]])
    bot.send_or_edit(
        chat_id,
        "Are you sure?",
        to_edit=update.effective_message.message_id,
        reply_markup=markup)


@restricted
def delete_bot(update: Update, context: FlowContext, to_edit: Bot):
    username = to_edit.username
    to_edit.disable(Bot.DisabledReason.banned)
    to_edit.save()
    context.bot.send_or_edit(
        update.effective_user.id,
        "Bot has been disabled and banned.",
        to_edit=update.effective_message.message_id
    )
    Statistic.of(update, 'disable', username, Statistic.IMPORTANT)


def change_category(update: Update, context: FlowContext, to_edit, category):
    uid = update.effective_user.id
    user = User.get(User.chat_id == uid)

    if uid == 918962:
        # Special for t3chno
        to_edit.category = category
        to_edit.save()
    else:
        if check_suggestion_limit(update, context, user):
            return
        Suggestion.add_or_update(user, 'category', to_edit, category.id)


def check_suggestion_limit(update: Update, context: FlowContext, user):
    cid = update.effective_chat.id
    if Suggestion.over_limit(user):
        context.bot.send_failure(
            cid,
            "You have reached the limit of {} suggestions. Please wait for "
            "the Moderators to approve of some of them.".format(settings.SUGGESTION_LIMIT))

        Statistic.of(update, 'hit the suggestion limit')
        return True
    return False


def change_suggestion(update: Update, context: FlowContext[PaginationModel], suggestion: Suggestion):
    mid = update.effective_message.message_id
    page_handover = context.view_model.page

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

    page_suggestion_model = SuggestionModel(suggestion, page_handover)
    buttons = [[
        ActionButton(captions.BACK, Actions.SWITCH_SUGGESTIONS_PAGE, PaginationModel(page_handover))
    ], [
        ActionButton(Actions.ACCEPT_SUGGESTION, page_suggestion_model),
        ActionButton(callback_action, page_suggestion_model),
        ActionButton(Actions.REJECT_SUGGESTION, page_suggestion_model)
    ]]

    reply_markup = InlineKeyboardMarkup(buttons)
    context.bot.send_or_edit(update.effective_chat.id,
                                       text,
                                       to_edit=mid,
                                       disable_web_page_preview=True,
                                       reply_markup=reply_markup)


def remove_keyword(update: Update, context: FlowContext, values):
    user = User.from_telegram_object(update.effective_user)
    if check_suggestion_limit(update, context, user):
        return
    to_edit = values.get('to_edit')
    kw = values.get('keyword')
    Suggestion.add_or_update(user=user, action='remove_keyword', subject=to_edit, value=kw.name)

    return RerouteToAction(Actions.SET_KEYWORDS, BotViewModel(to_edit))


@restricted
def accept_suggestion(update: Update, context: FlowContext[SuggestionModel]):
    suggestion = context.view_model.suggestion
    user = User.from_telegram_object(update.effective_user)
    suggestion.apply()

    if suggestion.action == 'offline':
        suggestion_text = '{} went {}.'.format(
            suggestion.subject.str_no_md,
            'offline' if suggestion.subject.offline else 'online')
    else:
        suggestion_text = str(suggestion)

    suggestion_text = suggestion_text[0].upper() + suggestion_text[1:]
    suggestion_text += '\nApproved by ' + user.markdown_short
    context.bot.send_message(settings.BOTLIST_NOTIFICATIONS_ID, suggestion_text,
                             parse_mode='markdown', disable_web_page_preview=True)

    if user != suggestion.user.chat_id:
        submittant_notification = '*Thank you* {}, your suggestion has been accepted:' \
                                  '\n\n{}'.format(util.escape_markdown(suggestion.user.first_name),
                                                  str(suggestion))
        try:
            context.bot.send_message(suggestion.user.chat_id, submittant_notification,
                                     parse_mode='markdown', disable_web_page_preview=True)
        except BadRequest:
            update.effective_message.reply_text(
                "Could not contact {}.".format(suggestion.user.markdown_short),
                parse_mode='markdown', disable_web_page_preview=True)


@restricted
def reject_suggestion(update: Update, context: FlowContext):
    update.message.reply_text("Coming soon")
    raise NotImplemented  # TODO
