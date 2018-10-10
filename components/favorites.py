import datetime
import logging
import re
import threading

import mdformat
import settings
import util
from actions import *
from actions import Actions
from const import DeepLinkingActions
from dialog import messages
from flow import RerouteToAction
from flow.context import FlowContext
from layouts import Layouts
from models import Bot, Favorite, Statistic, User, track_activity
from telegram import ForceReply, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, \
    Update
from telegram.ext import CallbackContext, ConversationHandler

logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.INFO)
log = logging.getLogger(__name__)


def add_favorite_handler(update: Update, context: FlowContext):
    uid = update.effective_user.id
    from components.basic import main_menu_buttons
    main_menu_markup = ReplyKeyboardMarkup(main_menu_buttons(uid in settings.MODERATORS))

    if context.args:
        query = ' '.join(context.args) if isinstance(context.args, list) else context.args
        try:
            # TODO: add multiple
            username = re.match(settings.REGEX_BOT_IN_TEXT, query).groups()[0]
            try:
                # TODO: get exact database matches for input without `@`
                item = Bot.by_username(username, include_disabled=True)

                return RerouteToAction(Actions.ADD_FAVORITE, BotViewModel())
                return add_favorite(context.bot, update, item)
            except Bot.DoesNotExist:
                buttons = [
                    InlineKeyboardButton(
                        "Yai!", callback_data=util.callback_for_action(Actions.ADD_ANYWAY,
                                                                       {'u': username})),
                    InlineKeyboardButton("Nay...",
                                         callback_data=util.callback_for_action(
                                             Actions.ADD_FAVORITE))
                ]
                reply_markup = InlineKeyboardMarkup([buttons])
                util.send_md_message(bot, uid,
                                     "{} is not in the @BotList. Do you want to add it to your {} anyway?".format(
                                         username, captions.FAVORITES),
                                     reply_markup=reply_markup)
        except AttributeError:
            # invalid bot username
            # TODO when does this happen?
            update.message.reply_text(
                util.failure("Sorry, but that is not a valid username. Please try again. /addfav"))
    else:
        buttons = [
            InlineKeyboardButton("Search inline", switch_inline_query_current_chat='')
        ]
        reply_markup = InlineKeyboardMarkup([buttons])

        bot.sendMessage(uid, messages.ADD_FAVORITE, reply_markup=ForceReply(selective=True))
    return ConversationHandler.END


def add_favorite(update: Update, context: FlowContext[BotNotifyModel]):
    context.view_model.update(update)
    item = context.view_model.bot
    uid = update.effective_user.id

    from components.basic import main_menu_buttons
    main_menu_markup = ReplyKeyboardMarkup(main_menu_buttons(uid in settings.MODERATORS))

    fav, created = Favorite.add(user=context.view_model.user, item=item)
    if created:
        Statistic.of(context.user, 'add-favorite', item.username)
        text = mdformat.love("{} added to your {}favorites.".format(
            fav.bot, '' if context.view_model.show_alert else '/')
        )
        if context.view_model.show_alert:
            update.callback_query.answer(text=text, show_alert=False)
        else:
            msg = context.bot.send_or_edit(uid, text, reply_markup=main_menu_markup)
            mid = msg.message_id
            util.wait(context.bot, update)
            send_favorites_list(update, context)
    else:
        text = mdformat.none_action(
            "{} is already a favorite of yours.{}".format(
                fav.bot, '' if context.view_model.show_alert else ' /favorites')
        )
        if context.view_model.show_alert:
            update.callback_query.answer(text=text, show_alert=False)
        else:
            context.bot.send_message(uid, text, reply_markup=main_menu_markup)
    return ConversationHandler.END


@track_activity('view-favorites', level=Statistic.ANALYSIS)
def send_favorites_list(update: Update, context: FlowContext):
    uid = update.effective_user.id
    user = User.from_update(update)

    t = threading.Thread(target=_too_many_favorites_handler, args=(update, context, user))
    t.start()

    favorites = Favorite.select_all(user)

    buttons = [
        [
            InlineKeyboardButton(captions.ADD_FAVORITE,
                                 callback_data=util.callback_for_action(Actions.ADD_FAVORITE)),
            InlineKeyboardButton(captions.REMOVE_FAVORITE,
                                 callback_data=util.callback_for_action(
                                     Actions.REMOVE_FAVORITE_MENU))
        ],
        [
            InlineKeyboardButton('Layout: ' + Layouts.get_caption(user.favorites_layout),
                                 callback_data=util.callback_for_action(
                                     Actions.TOGGLE_FAVORITES_LAYOUT,
                                     {'v': Layouts.get_next(user.favorites_layout)})),
        ],
        [
            InlineKeyboardButton(captions.SHARE, switch_inline_query=DeepLinkingActions.FAVORITES),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(buttons)

    if len(favorites) == 0:
        text = "You have no favorites yet."
    else:
        text = _favorites_categories_md(favorites, user.favorites_layout)

    context.bot.send_or_edit(uid, text, reply_markup=reply_markup)


@track_activity('toggled their favorites layout', level=Statistic.ANALYSIS)
def toggle_favorites_layout(bot, update, value):
    uid = update.effective_user.id
    user = User.from_update(update)
    user.favorites_layout = value
    user.save()
    send_favorites_list(bot, update)


def _favorites_categories_md(favorites, layout=None):
    text = messages.FAVORITES_HEADLINE + '\n'
    chunks = list()

    if layout == 'single':
        # text += '\n'
        favorites.sort(key=lambda x: x.bot.username)
        bots = [f.bot for f in favorites]
        total = len(bots) - 1
        for n, bot in enumerate(bots):
            if n < total:
                list_icon = '├'
            else:
                list_icon = '└'
            chunks.append('{} {}'.format(list_icon, str(bot)))
        all_favorites = '\n'.join(chunks)
        text += all_favorites

    else:
        # sort favorites by database order
        favorites.sort(key=lambda x: x.bot.category.order)

        current_category = None
        for n, f in enumerate(favorites):
            bot = f.bot
            category = bot.category

            try:
                if favorites[n + 1].bot.category != category:
                    list_icon = '└'
                else:
                    list_icon = '├'
            except IndexError:
                list_icon = '└'

            if current_category is None or category != current_category:
                category_no_bulletin = str(category)[1:]
                chunks.append('\n*{}*'.format(category_no_bulletin))

            chunks.append('{} {}'.format(list_icon, str(bot)))
            current_category = category

        all_favorites = '\n'.join(chunks)
        text += all_favorites

    return text


@track_activity('menu', 'remove favorite', Statistic.DETAILED)
def remove_favorite_menu(bot, update):
    uid = update.effective_user.id
    user = User.from_update(update)
    favorites = Favorite.select_all(user)

    fav_remove_buttons = [InlineKeyboardButton(
        '✖️ {}'.format(str(f.bot.username)),
        callback_data=util.callback_for_action(Actions.REMOVE_FAVORITE, {'id': f.id}))
        for f in favorites]
    buttons = util.build_menu(fav_remove_buttons, 2, header_buttons=[
        InlineKeyboardButton(captions.DONE,
                             callback_data=util.callback_for_action(Actions.SEND_FAVORITES))
    ])
    reply_markup = InlineKeyboardMarkup(buttons)
    bot.send_or_edit(uid, util.action_hint("Select favorites to remove"),
                               to_edit=update.effective_message.message_id,
                               reply_markup=reply_markup)


def _too_many_favorites_handler(update: Update, context: FlowContext):
    any_removed = False
    user = User.from_update(update)
    while too_many_favorites(user):
        oldest = Favorite.get_oldest(user)
        oldest.delete_instance()
        any_removed = True
        Statistic.of(update, 'had to lose a favorite because HE HAD TOO FUCKIN MANY 😬')
    if any_removed:
        txt = "You have too many favorites, _they do not fit into a single message_. That's why I removed your " \
              "oldest bot, *{}*, from your list of favorites.".format(oldest.bot if oldest.bot else oldest.custom_bot)
        context.bot.send_message(update.effective_user.id, txt)


def too_many_favorites(user):
    favs = Favorite.select_all(user)
    promo = max(len(messages.PROMOTION_MESSAGE), len(messages.FAVORITES_HEADLINE))
    message_length = len(_favorites_categories_md(favs)) + promo + 4
    return message_length > 4096


def add_custom(update: Update, context: FlowContext[AddCustomFavoriteModel]):
    uid = update.effective_user.id
    user = User.from_update(update)
    mid = update.effective_message.message_id
    from components.basic import main_menu_buttons
    main_menu_markup = ReplyKeyboardMarkup(main_menu_buttons(uid in settings.MODERATORS))

    try:
        fav = Favorite.get(custom_bot=context.view_model.username)
        util.send_or_edit_md_message(
            context.bot, uid, mdformat.none_action(
                "{} is already a favorite of yours. /favorites".format(fav.custom_bot)),
            to_edit=mid,
            reply_markup=main_menu_markup)
    except Favorite.DoesNotExist:
        fav = Favorite(user=user, custom_bot=context.view_model.username, date_added=datetime.date.today())
        fav.save()
        msg = context.bot.send_or_edit(uid,
                                                 mdformat.love("{} added to your /favorites.".format(
                                                     fav.custom_bot)),
                                                 to_edit=mid)
        mid = msg.message_id
        util.wait(context.bot, update)
        return RerouteToAction(Actions.SEND_FAVORITES)
    return ConversationHandler.END
