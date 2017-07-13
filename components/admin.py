# -*- coding: utf-8 -*-
import datetime
import logging
import re
from typing import Dict

import emoji
from telegram import ForceReply
from telegram import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup, TelegramError
from telegram.ext import ConversationHandler, Job

import captions
import helpers
import mdformat
import settings
import util
from const import *
from const import BotStates, CallbackActions
from custemoji import Emoji
from dialog import messages
from model import Bot
from model import Category
from model import Suggestion
from model import User
from util import restricted

logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.INFO)
log = logging.getLogger(__name__)


@restricted
def menu(bot, update):
    uid = util.uid_from_update(update)

    buttons = _admin_buttons(send_botlist_button=uid in settings.ADMINS)

    util.send_md_message(bot, uid, "🛃 Administration menu",
                         reply_markup=ReplyKeyboardMarkup(buttons, resize_keyboard=True))
    return BotStates.ADMIN_MENU


def _admin_buttons(send_botlist_button=True):
    n_unapproved = len(Bot.select().where(Bot.approved == False))
    n_suggestions = len(Suggestion.select_all())

    second_row = list()
    if n_unapproved > 0:
        second_row.append(KeyboardButton(captions.APPROVE_BOTS + ' ({} 🆕)'.format(n_unapproved)))
    if n_suggestions > 0:
        second_row.append(KeyboardButton(captions.APPROVE_SUGGESTIONS + ' ({} ⁉️)'.format(n_suggestions)))

    buttons = [[
        KeyboardButton(captions.EXIT),
        KeyboardButton(captions.REFRESH),
    ], [
        KeyboardButton(captions.FIND_OFFLINE),
        KeyboardButton(captions.SEND_CONFIG_FILES)
    ]]

    if send_botlist_button:
        buttons.insert(1, [KeyboardButton(captions.SEND_BOTLIST)])

    if len(second_row) > 0:
        buttons.insert(1, second_row)

    return buttons


@restricted
def _input_failed(bot, update, chat_data, text):
    chat_id = util.uid_from_update(update)
    util.send_message_failure(bot, chat_id, text)
    chat_data['add_bot_message'] = None


def _add_bot_to_chatdata(chat_data, category=None):
    new_bot = Bot(category=category)
    chat_data['add_bot'] = new_bot


def format_pending(text):
    return '{} {}'.format(captions.SUGGESTION_PENDING_EMOJI, text)


def _edit_bot_buttons(to_edit: Bot, pending_suggestions: Dict, is_moderator):
    bid = {'id': to_edit.id}

    def pending_or_caption(action, caption):
        return format_pending(str(pending_suggestions[action])) if action in pending_suggestions.keys() else str(
            caption)

    buttons = [
        InlineKeyboardButton(
            pending_or_caption('name', to_edit.name or "Set Name"),
            callback_data=util.callback_for_action(CallbackActions.EDIT_BOT_NAME, bid)
        ),
        InlineKeyboardButton(
            pending_or_caption('username', to_edit.username),
            callback_data=util.callback_for_action(CallbackActions.EDIT_BOT_USERNAME, bid)
        ),
        InlineKeyboardButton(
            # remove bulletin from category
            pending_or_caption('category', str(pending_suggestions.get('category') or to_edit.category)[1:]),
            callback_data=util.callback_for_action(CallbackActions.EDIT_BOT_SELECT_CAT, bid)
        ),
        InlineKeyboardButton(
            pending_or_caption('description',
                               "Change description" if to_edit.description else "Write a description"),
            callback_data=util.callback_for_action(CallbackActions.EDIT_BOT_DESCRIPTION, bid)
        ),
        InlineKeyboardButton(
            pending_or_caption('country', to_edit.country.emojized if to_edit.country else "Set country/language"),
            callback_data=util.callback_for_action(CallbackActions.EDIT_BOT_COUNTRY, bid)
        ),
        InlineKeyboardButton(
            pending_or_caption('extra', "Change extra text" if to_edit.extra else "Add an extra text"),
            callback_data=util.callback_for_action(CallbackActions.EDIT_BOT_EXTRA, bid)
        ),
        InlineKeyboardButton("Set keywords",
                             callback_data=util.callback_for_action(
                                 CallbackActions.EDIT_BOT_KEYWORDS, bid
                             )),
    ]

    toggleable_properties = [
        ('inlinequeries', '🔎', CallbackActions.EDIT_BOT_INLINEQUERIES),
        ('official', '🔹', CallbackActions.EDIT_BOT_OFFICIAL),
        ('offline', '💤', CallbackActions.EDIT_BOT_OFFLINE),
        ('spam', '🚮', CallbackActions.EDIT_BOT_SPAM),
    ]

    def toggle_button(property_name, emoji, callback_action):
        is_pending = property_name in pending_suggestions.keys()
        pending_emoji = captions.SUGGESTION_PENDING_EMOJI + ' ' if is_pending else ''
        active = bool(pending_suggestions[property_name]) if is_pending else bool(getattr(to_edit, property_name))
        active_emoji = '✔️' if active else Emoji.HEAVY_MULTIPLICATION_X
        caption = '{}{} {}'.format(pending_emoji, emoji, active_emoji)
        return InlineKeyboardButton(caption, callback_data=util.callback_for_action(
            callback_action, {'id': to_edit.id, 'value': not active}
        ))

    for toggle in toggleable_properties:
        buttons.append(toggle_button(*toggle))

    buttons.append(
        InlineKeyboardButton("Delete",
                             callback_data=util.callback_for_action(CallbackActions.CONFIRM_DELETE_BOT, bid)))

    header = [InlineKeyboardButton(captions.BACK_TO_CATEGORY,
                                   callback_data=util.callback_for_action(CallbackActions.SELECT_BOT_FROM_CATEGORY,
                                                                          {'id': to_edit.category.id})),
              InlineKeyboardButton(captions.REFRESH,
                                   callback_data=util.callback_for_action(CallbackActions.EDIT_BOT,
                                                                          {'id': to_edit.id}))
              ]

    footer = list()
    if is_moderator and len(pending_suggestions) > 0:
        footer.append(
            InlineKeyboardButton("🛃 Apply all changes",
                                 callback_data=util.callback_for_action(CallbackActions.APPLY_ALL_CHANGES,
                                                                        {'id': to_edit.id}))
        )

    return util.build_menu(buttons, n_cols=2, header_buttons=header, footer_buttons=footer)


@restricted
def edit_bot(bot, update, chat_data, to_edit=None):
    uid = util.uid_from_update(update)
    message_id = util.mid_from_update(update)
    user = User.from_update(update)

    if not to_edit:
        if update.message:
            command = update.message.text
            b_id = re.match(r'^/edit(\d+)$', command).groups()[0]

            try:
                to_edit = Bot.get(id=b_id)
            except Bot.DoesNotExist:
                update.message.reply_text(util.failure('No bot exists with this id.'))
                return
        else:
            util.send_message_failure(bot, uid, "An unexpected error occured.")
            return

    # chat_data['bot_to_edit'] = bot_to_edit

    pending_suggestions = Suggestion.pending_for_bot(to_edit, user)
    reply_markup = InlineKeyboardMarkup(_edit_bot_buttons(to_edit, pending_suggestions, uid in settings.MODERATORS))
    pending_text = '\n\n{} Some changes are pending approval.'.format(
        captions.SUGGESTION_PENDING_EMOJI) if pending_suggestions else ''
    msg = util.send_or_edit_md_message(
        bot, uid,
        "🛃 Edit {}{}".format(to_edit.detail_text, pending_text),
        to_edit=message_id, reply_markup=reply_markup)
    return


@restricted(strict=True)
def prepare_transmission(bot, update, chat_data):
    chat_id = util.uid_from_update(update)
    text = mdformat.action_hint(
        "Notify subscribers about this update?")
    reply_markup = InlineKeyboardMarkup([[
        InlineKeyboardButton("☑ Notifications", callback_data=util.callback_for_action(
            CallbackActions.SEND_BOTLIST, {'silent': False}
        )),
        InlineKeyboardButton("Silent", callback_data=util.callback_for_action(
            CallbackActions.SEND_BOTLIST, {'silent': True}
        ))],
        [
            InlineKeyboardButton("Re-send all Messages (delete all first)", callback_data=util.callback_for_action(
                CallbackActions.SEND_BOTLIST, {'silent': True, 're': True}))
        ]
    ])

    # # TODO
    # text = "Temporarily disabled"
    # reply_markup = None

    util.send_md_message(bot, chat_id, text,
                         reply_markup=reply_markup)


@restricted
def approve_suggestions(bot, update, page=0):
    uid = util.uid_from_update(update)
    suggestions = Suggestion.select_all()
    if page * settings.PAGE_SIZE_SUGGESTIONS_LIST >= len(suggestions):
        # old item deleted, list now too small
        page = page - 1 if page > 0 else 0
    start = page * settings.PAGE_SIZE_SUGGESTIONS_LIST
    end = start + settings.PAGE_SIZE_SUGGESTIONS_LIST

    has_prev_page = page > 0
    has_next_page = (page + 1) * settings.PAGE_SIZE_SUGGESTIONS_LIST < len(suggestions)

    suggestions = suggestions[start:end]

    if len(suggestions) == 0:
        util.send_or_edit_md_message(bot, uid, "No more suggestions available.",
                                     to_edit=util.mid_from_update(update))
        return

    buttons = []
    count = 1
    text = "Please choose suggestions to accept.\n"
    for x in suggestions:
        number = str(count) + '.'
        text += "\n{} {}".format(number, str(x))
        row = []

        # Should the suggestion be editable and is it too long?
        if x.action in Suggestion.TEXTUAL_ACTIONS:
            row.append(
                InlineKeyboardButton("{} {}📝".format(number, Emoji.WHITE_HEAVY_CHECK_MARK),
                                     callback_data=util.callback_for_action(CallbackActions.CHANGE_SUGGESTION,
                                                                            {'id': x.id, 'page': page})))
        else:
            row.append(
                InlineKeyboardButton("{} {}".format(number, Emoji.WHITE_HEAVY_CHECK_MARK),
                                     callback_data=util.callback_for_action(CallbackActions.ACCEPT_SUGGESTION,
                                                                            {'id': x.id, 'page': page})))

        row.append(
            InlineKeyboardButton("{} {}".format(number, Emoji.CROSS_MARK),
                                 callback_data=util.callback_for_action(CallbackActions.REJECT_SUGGESTION,
                                                                        {'id': x.id, 'page': page})))
        buttons.append(row)
        count += 1

    page_arrows = list()
    if has_prev_page:
        page_arrows.append(InlineKeyboardButton(Emoji.LEFTWARDS_BLACK_ARROW,
                                                callback_data=util.callback_for_action(
                                                    CallbackActions.SWITCH_SUGGESTIONS_PAGE,
                                                    {'page': page - 1})))
    if has_next_page:
        page_arrows.append(InlineKeyboardButton(Emoji.BLACK_RIGHTWARDS_ARROW,
                                                callback_data=util.callback_for_action(
                                                    CallbackActions.SWITCH_SUGGESTIONS_PAGE,
                                                    {'page': page + 1})))
    buttons.append(page_arrows)

    reply_markup = InlineKeyboardMarkup(buttons)

    util.send_or_edit_md_message(bot, uid, util.action_hint(text),
                                 reply_markup=reply_markup, to_edit=util.mid_from_update(update),
                                 disable_web_page_preview=True)
    return CallbackStates.APPROVING_BOTS


@restricted
def approve_bots(bot, update, page=0, override_list=None):
    chat_id = util.uid_from_update(update)

    if override_list:
        unapproved = override_list
    else:
        unapproved = Bot.select().where(Bot.approved == False).order_by(Bot.date_added)

    if page < 0:
        page = 0

    last_page = int((len(unapproved) - 1) / settings.PAGE_SIZE_BOT_APPROVAL)

    if page * settings.PAGE_SIZE_BOT_APPROVAL >= len(unapproved):
        # old item deleted, list now too small
        page = last_page
    start = page * settings.PAGE_SIZE_BOT_APPROVAL
    end = start + settings.PAGE_SIZE_BOT_APPROVAL

    has_prev_page = page > 0
    has_next_page = (page + 1) * settings.PAGE_SIZE_BOT_APPROVAL < len(unapproved)
    unapproved = unapproved[start:end]

    if len(unapproved) == 0:
        util.send_or_edit_md_message(bot, chat_id, "No more unapproved bots available. "
                                                   "Good job! (Is this the first time? 😂)",
                                     to_edit=util.mid_from_update(update))
        return

    buttons = list()
    for x in unapproved:
        first_row = [
            InlineKeyboardButton(x.username, url="http://t.me/{}".format(x.username[1:]))
        ]
        second_row = [
            InlineKeyboardButton('👍↑', callback_data=util.callback_for_action(
                CallbackActions.ACCEPT_BOT, {'id': x.id})),
            InlineKeyboardButton('👎↑', callback_data=util.callback_for_action(
                CallbackActions.REJECT_BOT, {'id': x.id, 'page': page, 'ntfc': True})),
            InlineKeyboardButton('🗑' + '↑', callback_data=util.callback_for_action(
                CallbackActions.REJECT_BOT, {'id': x.id, 'page': page, 'ntfc': False})),
            InlineKeyboardButton('👥🔀', callback_data=util.callback_for_action(
                CallbackActions.RECOMMEND_MODERATOR, {'id': x.id, 'page': page}))
        ]
        buttons.append(first_row)
        buttons.append(second_row)

    page_arrows = list()
    if has_prev_page:
        page_arrows.append(InlineKeyboardButton('⏮',
                                                callback_data=util.callback_for_action(
                                                    CallbackActions.SWITCH_APPROVALS_PAGE,
                                                    {'page': -1})))
        page_arrows.append(InlineKeyboardButton(Emoji.LEFTWARDS_BLACK_ARROW,
                                                callback_data=util.callback_for_action(
                                                    CallbackActions.SWITCH_APPROVALS_PAGE,
                                                    {'page': page - 1})))

    if has_prev_page or has_next_page:
        page_arrows.append(InlineKeyboardButton('·{}·'.format(page + 1),
                                                callback_data=util.callback_for_action(
                                                    CallbackActions.SWITCH_APPROVALS_PAGE,
                                                    {'page': page})))

    if has_next_page:
        page_arrows.append(InlineKeyboardButton(Emoji.BLACK_RIGHTWARDS_ARROW,
                                                callback_data=util.callback_for_action(
                                                    CallbackActions.SWITCH_APPROVALS_PAGE,
                                                    {'page': page + 1})))
        page_arrows.append(InlineKeyboardButton('⏭',
                                                callback_data=util.callback_for_action(
                                                    CallbackActions.SWITCH_APPROVALS_PAGE,
                                                    {'page': last_page})))
    buttons.append(page_arrows)

    reply_markup = InlineKeyboardMarkup(buttons)
    util.send_or_edit_md_message(bot, chat_id,
                                 util.action_hint(
                                     "Please select a bot you want to accept for the BotList"),
                                 reply_markup=reply_markup, to_edit=util.mid_from_update(update))
    return CallbackStates.APPROVING_BOTS


def recommend_moderator(bot, update, bot_in_question, page):
    uid = update.effective_user.id
    mid = util.mid_from_update(update)
    moderators = User.select().where((User.chat_id << settings.MODERATORS) & (User.chat_id != uid))
    buttons = [
        InlineKeyboardButton(u.first_name, callback_data=util.callback_for_action(
            CallbackActions.SELECT_MODERATOR,
            {'bot_id': bot_in_question.id, 'uid': u.id, 'page': page}))
        for u in moderators
        ]
    buttons.insert(0, InlineKeyboardButton(captions.BACK,
                                           callback_data=util.callback_for_action(CallbackActions.SWITCH_APPROVALS_PAGE,
                                                                                  {'page': page})))
    reply_markup = InlineKeyboardMarkup(util.build_menu(buttons, 1))
    text = mdformat.action_hint(
        "Select a moderator you think is better suited to evaluate the submission of {}.".format(str(bot_in_question)))
    util.send_or_edit_md_message(bot, uid, text, to_edit=mid, reply_markup=reply_markup)


def share_with_moderator(bot, update, bot_in_question, moderator):
    user = User.from_update(update)
    answer_text = mdformat.success(
        "I will ask {} to have a look at this submission.".format(moderator.plaintext))
    if update.callback_query:
        update.callback_query.answer(text=answer_text)

    buttons = [[
        InlineKeyboardButton('Yea, let me take this one!',
                             callback_data=util.callback_for_action(CallbackActions.APPROVE_REJECT_BOTS,
                                                                    {'id': bot_in_question.id}))
    ]]
    reply_markup = InlineKeyboardMarkup(buttons)
    text = "{} thinks that you have the means to inspect this bot submission:\n▶️ {}".format(
        user.markdown_short, bot_in_question
    )
    util.send_md_message(bot, moderator.chat_id, text, reply_markup=reply_markup, disable_web_page_preview=True)


@restricted
def edit_bot_category(bot, update, for_bot, callback_action=None):
    if callback_action is None:
        callback_action = CallbackActions.EDIT_BOT_CAT_SELECTED
    uid = util.uid_from_update(update)
    categories = Category.select().order_by(Category.name.asc()).execute()

    buttons = util.build_menu([InlineKeyboardButton(
        '{}{}'.format(emoji.emojize(c.emojis, use_aliases=True), c.name),
        callback_data=util.callback_for_action(
            callback_action, {'cid': c.id, 'bid': for_bot.id})) for c in categories], 2)
    return util.send_or_edit_md_message(bot, uid, util.action_hint("Please select a category" +
                                                                   (" for {}".format(for_bot) if for_bot else '')),
                                        to_edit=util.mid_from_update(update),
                                        reply_markup=InlineKeyboardMarkup(buttons))


@restricted
def accept_bot_submission(bot, update, of_bot: Bot, category):
    uid = util.uid_from_update(update)
    message_id = util.mid_from_update(update)
    user = User.from_update(update)

    try:
        of_bot.category = category
        of_bot.date_added = datetime.date.today()
        of_bot.approved = True
        of_bot.approved_by = user
        of_bot.save()

        buttons = [[InlineKeyboardButton("Edit {} details".format(of_bot.username),
                                         callback_data=util.callback_for_action(CallbackActions.EDIT_BOT,
                                                                                {'id': of_bot.id}))]]
        reply_markup = InlineKeyboardMarkup(buttons)

        util.send_or_edit_md_message(bot, uid, "{} has been accepted to the Botlist. "
                                               "The group will receive a notification in {} minutes, giving you "
                                               "enough time to edit the details.".format(of_bot,
                                                                                         settings.BOT_ACCEPTED_IDLE_TIME),
                                     to_edit=message_id, reply_markup=reply_markup)

        log_msg = "{} accepted by {}.".format(of_bot.username, uid)

        # notify submittant
        if of_bot.submitted_by != user:
            try:
                bot.sendMessage(of_bot.submitted_by.chat_id,
                                util.success(messages.ACCEPTANCE_PRIVATE_MESSAGE.format(of_bot.username)))
                log_msg += "\nUser {} was notified.".format(str(of_bot.submitted_by))
            except TelegramError:
                log_msg += "\nUser {} could NOT be contacted/notified in private.".format(str(of_bot.submitted_by))

        log.info(log_msg)
    except:
        util.send_message_failure(bot, uid, "An error has occured. Bot not added.")


@restricted
def send_config_files(bot, update):
    log.info("Sending config files...")
    chat_id = util.uid_from_update(update)
    bot.sendDocument(chat_id, open('files/intro_en.txt', 'rb'), filename="intro_en.txt")
    bot.sendDocument(chat_id, open('files/intro_es.txt', 'rb'), filename="intro_es.txt")
    bot.sendDocument(chat_id, open('files/new_bots_list.txt', 'rb'), filename="new_bots_list.txt")
    bot.sendDocument(chat_id, open('files/category_list.txt', 'rb'), filename="category_list.txt")
    bot.sendDocument(chat_id, open('files/commands.txt', 'rb'), filename="commands.txt")


@restricted
def send_offline(bot, update):
    chat_id = util.uid_from_update(update)
    offline = Bot.select().where(Bot.offline == True)
    if len(offline) > 0:
        text = "Offline Bots:\n\n"
        text += '\n'.join(["{} — /edit{}".format(str(b), b.id) for b in offline])
    else:
        text = "No bots are offline."
    util.send_md_message(bot, chat_id, text)


@restricted
def reject_bot_submission(bot, update, to_reject=None, verbose=True, notify_submittant=True):
    uid = util.uid_from_update(update)
    user = User.from_update(update)

    if to_reject is None:
        if not update.message.reply_to_message:
            update.message.reply_text(util.failure("You must reply to a message of mine."))
            return
        text = update.message.reply_to_message.text

        try:
            username = re.match(settings.REGEX_BOT_IN_TEXT, text).groups()[0]
        except AttributeError:
            log.info("No username in the message that was replied to.")
            # no bot username, ignore update
            return

        try:
            to_reject = Bot.by_username(username)
        except Bot.DoesNotExist:
            log.info("Rejection failed: could not find {}".format(username))
            return

        if to_reject.approved is True:
            bot.sendMessage(uid, util.failure(
                "{} has already been accepted, so it cannot be rejected anymore.".format(username)))
            return

    log_msg = "{} rejected by {}.".format(to_reject.username, user)
    notification_successful = None
    if notify_submittant:
        try:
            bot.sendMessage(to_reject.submitted_by.chat_id,
                            util.failure(messages.REJECTION_PRIVATE_MESSAGE.format(to_reject.username)))
            log_msg += "\nUser {} was notified.".format(str(to_reject.submitted_by))
            notification_successful = True
        except TelegramError:
            log_msg += "\nUser {} could NOT be contacted/notified in private.".format(str(to_reject.submitted_by))
            notification_successful = False
    to_reject.delete_instance()
    log.info(log_msg)

    text = util.success("{} rejected.".format(to_reject.username))
    if notification_successful is True:
        text += " User {} was notified.".format(to_reject.submitted_by.plaintext)
    elif notification_successful is False:
        text += ' ' + mdformat.failure("Could not contact {}.".format(to_reject.submitted_by.plaintext))
    else:
        text += " No notification sent."

    if verbose:
        bot.sendMessage(uid, text)

    if update.callback_query:
        update.callback_query.answer(text=text)


@restricted
def ban_handler(bot, update, args, ban_state: bool):
    if args:
        query = ' '.join(args) if isinstance(args, list) else args

        try:
            user = User.by_username(query)
        except User.DoesNotExist:
            update.message.reply_text("This user does not exist.")
            return

        ban_user(bot, update, user, ban_state)
    else:
        # no search term
        update.message.reply_text(messages.UNBAN_MESSAGE if ban_state else messages.BAN_MESSAGE,
                                  reply_markup=ForceReply(selective=True))
    return ConversationHandler.END


@restricted
def ban_user(bot, update, user: User, ban_state: bool):
    if user.banned and ban_state is True:
        update.message.reply_text(mdformat.none_action("User {} is already banned.".format(user)))
        return
    if not user.banned and ban_state is False:
        update.message.reply_text(mdformat.none_action("User {} is not banned.".format(user)))
        return
    user.banned = ban_state
    if ban_state is True:
        users_bots = Bot.select().where(
            (Bot.approved == False) &
            (Bot.submitted_by == user)
        )
        for b in users_bots:
            b.delete_instance()
        update.message.reply_text(mdformat.success("User {} banned and all bot submissions removed.".format(user)))
    else:
        update.message.reply_text(mdformat.success("User {} unbanned.".format(user)))
    user.save()


def last_update_job(bot, job: Job):
    ## SEND A MESSAGE
    # user_ids = [u.chat_id for u in User.select()]
    # not_sent = list()
    # for uid in user_ids:
    #     import bot as botlistbot
    #     try:
    #         bot.sendMessage(uid, "Hey, check out my new Keyboard! 😍",
    #                         reply_markup=ReplyKeyboardMarkup(botlistbot._main_menu_buttons()))
    #     except TelegramError:
    #         not_sent.append(uid)
    # pprint(not_sent)

    last_update = helpers.get_channel().last_update
    if last_update:
        today = datetime.date.today()
        delta = datetime.timedelta(days=settings.BOT_CONSIDERED_NEW - 1)
        difference = today - last_update

        if difference > delta:
            for a in settings.MODERATORS:
                try:
                    bot.sendMessage(a, "Last @BotList update was {} days ago. UPDATE NOW YOU CARNT! /admin".format(
                        difference.days))
                except TelegramError:
                    pass


@restricted
def apply_all_changes(bot, update, chat_data, to_edit):
    user = User.from_update(update)

    user_suggestions = Suggestion.select_all_of_user(user)
    for suggestion in user_suggestions:
        suggestion.apply()

    refreshed_bot = Bot.get(id=to_edit.id)
    edit_bot(bot, update, chat_data, refreshed_bot)
