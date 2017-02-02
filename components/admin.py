import codecs

import datetime
from pprint import pprint

import emoji
import re
from telegram.error import BadRequest

from telegram import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ConversationHandler
from telegram.ext.dispatcher import run_async

import captions
import const
import helpers
import util
from const import *
from const import BotStates, CallbackActions
from custemoji import Emoji
from model import Bot, Category
from model import Category
from model import Channel
from model import Suggestion
from util import restricted


@restricted
def menu(bot, update):
    chat_id = util.cid_from_update(update)
    n_unapproved = len(Bot.select().where(Bot.approved == False))
    n_suggestions = len(Suggestion.select())

    first_row = list()
    if n_unapproved > 0:
        first_row.append(KeyboardButton(captions.APPROVE_BOTS + ' ({} 🆕)'.format(n_unapproved)))
    if n_suggestions > 0:
        first_row.append(KeyboardButton(captions.APPROVE_SUGGESTIONS + ' ({})'.format(n_suggestions)))

    buttons = [[
        KeyboardButton(captions.SEND_BOTLIST)
    ], [
        KeyboardButton(captions.FIND_OFFLINE),
        KeyboardButton(captions.SEND_CONFIG_FILES)
    ]]

    if len(first_row) > 0:
        buttons.insert(0, first_row)
    util.send_md_message(bot, chat_id, "Administration menu.",
                         reply_markup=ReplyKeyboardMarkup(buttons, resize_keyboard=True))
    return BotStates.ADMIN_MENU


@restricted
def _input_failed(bot, update, chat_data, text):
    chat_id = util.cid_from_update(update)
    util.send_message_failure(bot, chat_id, text)
    chat_data['add_bot_message'] = None


def _add_bot_to_chatdata(chat_data, category=None):
    new_bot = Bot(category=category)
    chat_data['add_bot'] = new_bot


# @restricted
# def add_bot(bot, update, chat_data, category=None):
#     chat_id = util.cid_from_update(update)
#     text_input = None
#     if update.message:
#         text_input = update.message.text
#     from bot import select_category
#     if not category:
#         msg = select_category(bot, update, CallbackActions.ADD_BOT_SELECT_CAT)
#         chat_data['add_bot_message'] = msg.message_id
#         return  # BotStates.ADMIN_ADDING_BOT
#     text = ""
#     reply_markup = None
#
#     new_bot = chat_data.get('add_bot', None)
#     if new_bot is None:
#         _add_bot_to_chatdata(chat_data, category)
#         new_bot = chat_data['add_bot']
#         text += "*{}* category selected.\n\n".format(category)
#
#     if new_bot.username is None:
#         if text_input:
#             username = helpers.validate_username(text_input)
#             if username:
#                 new_bot.username = username
#                 text += "Username *{}* chosen.\n\n".format(username)
#             else:
#                 return _input_failed(bot, update, chat_id, "Invalid username. Please try again.")
#         else:
#             text += util.action_hint("Please send me the *@username* of the bot to add")
#
#     msg = util.send_or_edit_md_message(bot, chat_id, text, to_edit=chat_data['add_bot_message'],
#                                        reply_markup=reply_markup)
#     chat_data['add_bot'] = new_bot
#     return BotStates.ADMIN_ADDING_BOT


def _edit_bot_buttons(to_edit: Bot):
    bid = {'id': to_edit.id}
    buttons = [
        InlineKeyboardButton(to_edit.name if to_edit.name else "Set Name", callback_data=util.callback_for_action(
            CallbackActions.EDIT_BOT_NAME, bid
        )),
        InlineKeyboardButton(to_edit.username, callback_data=util.callback_for_action(
            CallbackActions.EDIT_BOT_USERNAME, bid
        )),
        InlineKeyboardButton(str(to_edit.category), callback_data=util.callback_for_action(
            CallbackActions.EDIT_BOT_SELECT_CAT, bid
        )),
        InlineKeyboardButton("Change description" if to_edit.description else "Write a description",
                             callback_data=util.callback_for_action(
                                 CallbackActions.EDIT_BOT_DESCRIPTION, bid
                             )),
        InlineKeyboardButton(to_edit.country.emojized if to_edit.country else "Set country/language",
                             callback_data=util.callback_for_action(CallbackActions.EDIT_BOT_COUNTRY, bid)),
        InlineKeyboardButton("Change extra text" if to_edit.extra else "Add an extra text",
                             callback_data=util.callback_for_action(
                                 CallbackActions.EDIT_BOT_EXTRA, bid
                             )),
    ]

    # inlinequeries
    if to_edit.inlinequeries:
        buttons.append(
            InlineKeyboardButton("🔎 {}".format(Emoji.WHITE_HEAVY_CHECK_MARK), callback_data=util.callback_for_action(
                CallbackActions.EDIT_BOT_INLINEQUERIES, {'id': to_edit.id, 'value': False}
            )))
    else:
        buttons.append(
            InlineKeyboardButton("🔎 {}".format(Emoji.HEAVY_MULTIPLICATION_X), callback_data=util.callback_for_action(
                CallbackActions.EDIT_BOT_INLINEQUERIES, {'id': to_edit.id, 'value': True}
            )))

    # official
    if to_edit.official:
        buttons.append(
            InlineKeyboardButton("🔹 {}".format(Emoji.WHITE_HEAVY_CHECK_MARK), callback_data=util.callback_for_action(
                CallbackActions.EDIT_BOT_OFFICIAL, {'id': to_edit.id, 'value': False}
            )))
    else:
        buttons.append(
            InlineKeyboardButton("🔹 {}".format(Emoji.HEAVY_MULTIPLICATION_X), callback_data=util.callback_for_action(
                CallbackActions.EDIT_BOT_OFFICIAL, {'id': to_edit.id, 'value': True}
            )))

    # offline
    if to_edit.offline:
        buttons.append(
            InlineKeyboardButton("💤 {}".format(Emoji.WHITE_HEAVY_CHECK_MARK), callback_data=util.callback_for_action(
                CallbackActions.EDIT_BOT_OFFLINE, {'id': to_edit.id, 'value': False}
            )))
    else:
        buttons.append(
            InlineKeyboardButton("💤 {}".format(Emoji.HEAVY_MULTIPLICATION_X), callback_data=util.callback_for_action(
                CallbackActions.EDIT_BOT_OFFLINE, {'id': to_edit.id, 'value': True}
            )))

    buttons.append(
        InlineKeyboardButton("Delete", callback_data=util.callback_for_action(CallbackActions.CONFIRM_DELETE_BOT, bid)))

    return util.build_menu(buttons, n_cols=2)


@restricted
def edit_bot(bot, update, chat_data, bot_to_edit=None):
    chat_id = util.cid_from_update(update)
    message_id = util.mid_from_update(update)

    if not bot_to_edit:
        if update.message:
            command = update.message.text
            b_id = re.match(r'^/edit(\d+)$', command).groups()[0]

            # TODO: always treats last message as bot to edit
            pprint(b_id)

            bot_to_edit = Bot.get(id=b_id)
        else:
            util.send_message_failure(bot, chat_id, "An unexpected error occured.")
            return

    # chat_data['bot_to_edit'] = bot_to_edit

    reply_markup = InlineKeyboardMarkup(_edit_bot_buttons(bot_to_edit))
    util.send_or_edit_md_message(
        bot, chat_id,
        util.action_hint("Edit the properties of {}:{}".format(
            bot_to_edit,
            ('\n\n*Description:*\n{}'.format(bot_to_edit.description) if bot_to_edit.description else '')
        )),
        to_edit=message_id, reply_markup=reply_markup)


@restricted
def prepare_transmission(bot, update, chat_data):
    chat_id = util.cid_from_update(update)
    reply_markup = InlineKeyboardMarkup([[
        InlineKeyboardButton("☑ Update messages", callback_data=util.callback_for_action(
            CallbackActions.SEND_BOTLIST
        )),
        InlineKeyboardButton("I deleted all messages. Re-Send now", callback_data=util.callback_for_action(
            CallbackActions.RESEND_BOTLIST
        )),
    ]])
    util.send_md_message(bot, chat_id, "You have the option to update the messages, or re-send the whole botlist.",
                         reply_markup=reply_markup)


@restricted
@run_async
def send_botlist(bot, update, chat_data, resend=False):
    chat_id = util.cid_from_update(update)
    message_id = util.mid_from_update(update)
    channel = Channel.get(Channel.username == const.SELF_CHANNEL_USERNAME)

    def notify_admin(txt):
        util.send_or_edit_md_message(bot, chat_id, Emoji.HOURGLASS_WITH_FLOWING_SAND + ' ' + txt,
                                     to_edit=message_id,
                                     disable_web_page_preview=True)

    if resend:
        notify_admin("Sending intro GIF...")
        bot.sendDocument(channel.chat_id, open("assets/gif/animation.gif", 'rb'), timeout=120)

    with codecs.open('files/intro.txt', 'r', 'utf-8') as f:
        intro = f.read()

    notify_admin("Sending channel intro text...")
    try:
        if resend:
            intro_msg = util.send_md_message(bot, channel.chat_id, intro,
                                             timeout=120)
        else:
            intro_msg = util.send_or_edit_md_message(bot, channel.chat_id, intro,
                                                     to_edit=channel.intro_mid,
                                                     timeout=120,
                                                     disable_web_page_preview=True)
        channel.intro_mid = intro_msg.message_id
    except BadRequest:
        # message not modified
        pass

    counter = 0
    all_categories = Category.select()
    n = len(all_categories)
    for c in all_categories:
        counter += 1
        if counter % 5 == 1:
            notify_admin("Sending/Updating categories *{} to {}* ({} total)...".format(
                counter,
                n if counter + 4 > n else counter + 4,
                n
            ))

        # Bots!
        cat_bots = Bot.select().where(Bot.category == c, Bot.approved == True)
        text = '*' + str(c) + '*\n'
        text += '\n'.join([str(b) for b in cat_bots])

        # add "Details" deep-linking button
        reply_markup = None
        buttons = list()
        # if any([b for b in cat_bots if b.description is not None]):
        buttons.append(
            InlineKeyboardButton("Details", url="https://t.me/{}?start={}".format(
                const.SELF_BOT_NAME, c.id)))

        # buttons.append(
        #     InlineKeyboardButton("Permalink", callback_data=util.callback_for_action(CallbackActions.PERMALINK,
        #                                                                              {'cid': c.id})))
        # buttons.append(InlineKeyboardButton("Test", url="http://t.me/{}?start={}".format(
        #     const.SELF_CHANNEL_USERNAME, c.current_message_id)))
        reply_markup = InlineKeyboardMarkup([buttons])
        try:
            if resend:
                msg = util.send_md_message(bot, channel.chat_id, text, reply_markup=reply_markup, timeout=120)
            else:
                msg = util.send_or_edit_md_message(bot, channel.chat_id, text, reply_markup=reply_markup,
                                                   to_edit=c.current_message_id, timeout=120,
                                                   disable_web_page_preview=True)
            c.current_message_id = msg.message_id
            channel.last_message_id = msg.message_id
            c.save()
        except BadRequest:
            # message not modified
            pass

    with codecs.open('files/new_bots_list.txt', 'r', 'utf-8') as f:
        new_bots_list = f.read()

    # build list of newly added bots
    new_bots = Bot.select().where(
        (Bot.approved == True) & (
            Bot.date_added.between(
                datetime.date.today() - datetime.timedelta(days=const.BOT_CONSIDERED_NEW),
                datetime.date.today()
            )
        ))

    # insert spaces and the name of the bot
    new_bots_list = new_bots_list.format('\n'.join(['     ' + str(b) for b in new_bots]))
    try:
        if resend:
            new_bots_msg = util.send_md_message(bot, channel.chat_id, new_bots_list, timeout=120)
        else:
            new_bots_msg = util.send_or_edit_md_message(bot, channel.chat_id, new_bots_list,
                                                        to_edit=channel.new_bots_mid,
                                                        timeout=120, disable_web_page_preview=True)
        channel.new_bots_mid = new_bots_msg.message_id
    except BadRequest:
        # message not modified
        pass

    # generate category links to previous messages
    categories = '\n'.join(["[{}](https://t.me/{}/{})".format(
        str(c),
        channel.username,
        c.current_message_id
    ) for c in Category.select()])
    with codecs.open('files/category_list.txt', 'r', 'utf-8') as f:
        category_list = f.read()

    # insert placeholders in categories list
    category_list = category_list.format(
        "http://t.me/{}/{}".format(channel.username, channel.intro_mid), categories,
        "http://t.me/{}/{}".format(channel.username, channel.new_bots_mid),
        datetime.date.today().strftime("%d-%m-%Y")
    )
    try:
        if resend:
            category_list_msg = util.send_md_message(bot, channel.chat_id, category_list, timeout=120)
        else:
            category_list_msg = util.send_or_edit_md_message(bot, channel.chat_id, category_list,
                                                             to_edit=channel.category_list_mid, timeout=120,
                                                             disable_web_page_preview=True)
        channel.category_list_mid = category_list_msg.message_id
    except BadRequest:
        # message not modified
        pass

    channel.save()
    util.send_or_edit_md_message(bot, chat_id, util.success("Botlist updated successfully."),
                                 to_edit=message_id)


@restricted
def approve_suggestions(bot, update):
    chat_id = util.cid_from_update(update)
    suggestions = Suggestion.select()

    if len(suggestions) == 0:
        util.send_or_edit_md_message(bot, chat_id, "No more suggestions available.",
                                     to_edit=util.mid_from_update(update))
        return

    buttons = []
    count = 1
    text = "Please choose suggestions to accept.\n"
    for x in suggestions:
        text += "\n{}.) {}".format(count, str(x))
        buttons.append([
            InlineKeyboardButton("{}.) {}".format(str(count), Emoji.WHITE_HEAVY_CHECK_MARK),
                                 callback_data=util.callback_for_action(CallbackActions.ACCEPT_SUGGESTION,
                                                                        {'id': x.id})),
            InlineKeyboardButton(Emoji.CROSS_MARK,
                                 callback_data=util.callback_for_action(CallbackActions.REJECT_SUGGESTION,
                                                                        {'id': x.id}))
        ])
        count += 1

    reply_markup = InlineKeyboardMarkup(buttons)

    util.send_or_edit_md_message(bot, chat_id, util.action_hint(text),
                                 reply_markup=reply_markup, to_edit=util.mid_from_update(update))
    return CallbackStates.APPROVING_BOTS


@restricted
def approve_bots(bot, update):
    chat_id = util.cid_from_update(update)
    unapproved = Bot.select().where(Bot.approved == False)

    if len(unapproved) == 0:
        util.send_or_edit_md_message(bot, chat_id, "No more unapproved bots available.",
                                     to_edit=util.mid_from_update(update))
        return

    buttons = []
    for x in unapproved:
        buttons.append([
            InlineKeyboardButton(x.username,
                                 callback_data=util.callback_for_action(CallbackActions.ACCEPT_BOT, {'id': x.id})),
            InlineKeyboardButton(Emoji.CROSS_MARK,
                                 callback_data=util.callback_for_action(CallbackActions.REJECT_BOT, {'id': x.id}))
        ])

    reply_markup = InlineKeyboardMarkup(buttons)

    util.send_or_edit_md_message(bot, chat_id,
                                 util.action_hint("Please select a bot you want to accept for the BotList."),
                                 reply_markup=reply_markup, to_edit=util.mid_from_update(update))
    return CallbackStates.APPROVING_BOTS


@restricted
def edit_bot_category(bot, update, for_bot, callback_action=None):
    if callback_action is None:
        callback_action = CallbackActions.EDIT_BOT_CAT_SELECTED
    chat_id = util.cid_from_update(update)
    categories = Category.select().order_by(Category.name.asc()).execute()

    buttons = util.build_menu([InlineKeyboardButton(
        '{}{}'.format(emoji.emojize(c.emojis, use_aliases=True), c.name),
        callback_data=util.callback_for_action(
            callback_action, {'cid': c.id, 'bid': for_bot.id})) for c in categories], 2)
    return util.send_or_edit_md_message(bot, chat_id, util.action_hint("Please select a category" +
                                                                       (" for {}".format(for_bot) if for_bot else '')),
                                        to_edit=util.mid_from_update(update),
                                        reply_markup=InlineKeyboardMarkup(buttons))


@restricted
def accept_bot_submission(bot, update, of_bot: Bot, category):
    chat_id = util.cid_from_update(update)
    message_id = util.mid_from_update(update)

    try:
        of_bot.category = category
        of_bot.approved = True
        of_bot.save()

        buttons = [[InlineKeyboardButton("Edit {} details".format(of_bot.username),
                                         callback_data=util.callback_for_action(CallbackActions.EDIT_BOT,
                                                                                {'id': of_bot.id}))]]
        reply_markup = InlineKeyboardMarkup(buttons)

        util.send_or_edit_md_message(bot, chat_id, "{} has been accepted to the Botlist.".format(of_bot),
                                     to_edit=message_id, reply_markup=reply_markup)
    except:
        util.send_message_failure(bot, chat_id, "An error has occured. Bot not added.")


@restricted
def send_config_files(bot, update):
    chat_id = util.cid_from_update(update)
    bot.sendDocument(chat_id, open('files/category_list.txt', 'rb'), filename="category_list.txt")
    bot.sendDocument(chat_id, open('files/intro.txt', 'rb'), filename="intro.txt")
    bot.sendDocument(chat_id, open('files/new_bots_list.txt', 'rb'), filename="new_bots_list.txt")
    bot.sendDocument(chat_id, open('files/commands.txt', 'rb'), filename="new_bots_list.txt")


@restricted
def send_offline(bot, update):
    chat_id = util.cid_from_update(update)
    offline = Bot.select().where(Bot.offline == True)
    if len(offline) > 0:
        text = "Offline Bots:\n\n"
        text += '\n'.join(["{} — /edit{}".format(str(b), b.id) for b in offline])
    else:
        text = "No bots are offline."
    util.send_md_message(bot, chat_id, text)
