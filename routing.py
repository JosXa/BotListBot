import re
from functools import partial
from logzero import logger as log

import components.basic
import settings
from actions import *
from components import (admin, basic, botlist, botlistchat, botproperties, broadcasts, contributions, eastereggs,
                        explore, favorites, help, inlinequeries)
from components.basic import all_handler
from components.explore import select_category, send_bot_details, send_category, send_new_bots
from components.misc import access_token, set_notifications, t3chnostats
from components.search import search_handler, search_query
from components.userbot import BotChecker
from const import BotStates
from dialog import messages
from dialog.hints import HINTS
from flow import RerouteToAction
from flow.context import FlowContext
from flow.handlers.actionhandler import ActionHandler
from flow.handlers.choseninlineactionhandler import ChosenInlineActionHandler
from flow.handlers.inlinequeryactionhandler import InlineQueryActionHandler
from misc import manage_subscription
from models import Statistic
from telegram import Update
from telegram.ext import (CallbackContext, CommandHandler, ConversationHandler, Dispatcher,
                          DispatcherHandlerStop, Filters, InlineQueryHandler,
                          MessageHandler, RegexHandler)


def remove_favorite(update: Update, context: FlowContext[RemoveFavoriteModel]):
    context.view_model.favorite.delete_instance()

    if context.view_model.show_details:
        return RerouteToAction(Actions.SEND_BOT_DETAILS, view_model=BotViewModel())
    else:
        return RerouteToAction(Actions.REMOVE_FAVORITE_MENU)


def forward_router(bot, update, chat_data):
    text = update.effective_message.text

    # match first username in forwarded message
    try:
        username = re.match(settings.REGEX_BOT_IN_TEXT, text).groups()[0]
        if username == '@' + settings.SELF_BOT_NAME:
            return  # ignore

        item = Bot.get(Bot.username == username)

        send_bot_details(bot, update, chat_data, item)

    except (AttributeError, TypeError, Bot.DoesNotExist):
        pass  # no valid username in forwarded message


def reply_router(update: Update, context: FlowContext):
    text = update.effective_message.reply_to_message.text

    if text == messages.ADD_FAVORITE:
        query = update.message.text
        favorites.add_favorite_handler(update, context, query)
    elif text == messages.SEARCH_MESSAGE:
        query = update.message.text
        search_query(update, context)

    # BOTPROPERTIES
    bot_properties = ['description', 'extra', 'name', 'username']
    try:
        partition = text.partition(messages.BOTPROPERTY_STARTSWITH)
    except AttributeError:
        return
    if partition[1] != '':
        bot_property = next(p for p in bot_properties if partition[2].startswith(p))
        # Reply for setting a bot property
        botproperties.set_text_property(update, context, bot_property)
        print('raising...')
        print(partition)
        print(partition[1])
        raise DispatcherHandlerStop
    elif text == messages.BAN_MESSAGE:
        query = update.message.text
        admin.ban_handler(update, context, True)
    elif text == messages.UNBAN_MESSAGE:
        query = update.message.text
        admin.ban_handler(update, context, False)


def register(dp: Dispatcher, bot_checker: BotChecker):
    # admin.register(dp)
    basic.register(dp)

    # botlist.register(dp)
    # botlistchat.register(dp)
    # botproperties.register(dp)
    # broadcasts.register(dp)
    # contributions.register(dp)
    # eastereggs.register(dp)
    # explore.register(dp)
    # favorites.register(dp)
    # help.register(dp)
    # inlinequeries.register(dp)

    def add(*args, **kwargs):
        dp.add_handler(*args, **kwargs)

    ### ActionHandlers
    add(ActionHandler(Actions.DELETE_CONVERSATION, botlistchat.delete_conversation))
    add(ActionHandler(Actions.HELP, help.help))
    add(ActionHandler(Actions.CONTRIBUTING, help.contributing))
    add(ActionHandler(Actions.EXAMPLES, help.examples))
    add(ActionHandler(Actions.SELECT_CATEGORY, select_category))
    add(ActionHandler(Actions.SELECT_BOT_FROM_CATEGORY, send_category))
    add(ActionHandler(Actions.SEND_BOT_DETAILS, send_bot_details))
    add(ActionHandler(Actions.TOGGLE_FAVORITES_LAYOUT, favorites.toggle_favorites_layout))
    add(ActionHandler(Actions.ADD_FAVORITE, favorites.add_favorite_handler))
    add(ActionHandler(Actions.REMOVE_FAVORITE_MENU, favorites.remove_favorite_menu))
    add(ActionHandler(Actions.REMOVE_FAVORITE, remove_favorite))  # TODO soon
    add(ActionHandler(Actions.SEND_FAVORITES, favorites.send_favorites_list))
    add(ActionHandler(Actions.ADD_ANYWAY, favorites.add_custom))
    add(ActionHandler(Actions.ADD_TO_FAVORITES, favorites.add_favorite))
    add(ActionHandler(Actions.APPROVE_REJECT_BOTS, admin.approve_bots))
    add(ActionHandler(Actions.ACCEPT_BOT, admin.accept_bot_submission))
    add(ActionHandler(Actions.BOT_ACCEPTED, admin.edit_bot_category))  # TODO: notify_group-submission_accepted job
    add(ActionHandler(Actions.RECOMMEND_MODERATOR, admin.recommend_moderator))
    add(ActionHandler(Actions.SELECT_MODERATOR, admin.share_with_moderator))
    add(ActionHandler(Actions.REJECT_BOT, admin.reject_bot_submission))
    add(ActionHandler(Actions.BOT_ACCEPTED, admin.accept_bot_submission))
    add(ActionHandler(Actions.COUNT_THANK_YOU, basic.count_thank_you))
    add(ActionHandler(Actions.EDIT_BOT, admin.edit_bot))
    add(ActionHandler(Actions.EDIT_BOT_SELECT_CAT, admin.edit_bot_category))
    add(ActionHandler(Actions.EDIT_BOT_CAT_SELECTED, botproperties.change_category))
    add(ActionHandler(Actions.EDIT_BOT_COUNTRY, botproperties.set_country_menu))
    add(ActionHandler(Actions.SET_COUNTRY, botproperties.set_country))
    add(ActionHandler(Actions.EDIT_BOT_DESCRIPTION, partial(botproperties.set_text_property, 'description')))
    add(ActionHandler(Actions.EDIT_BOT_EXTRA, partial(botproperties.set_text_property, 'extra')))
    add(ActionHandler(Actions.EDIT_BOT_NAME, partial(botproperties.set_text_property, 'name')))
    add(ActionHandler(Actions.EDIT_BOT_USERNAME, partial(botproperties.set_text_property, 'username')))
    add(ActionHandler(Actions.APPLY_ALL_CHANGES, admin.apply_all_changes))
    add(ActionHandler(Actions.EDIT_BOT_INLINEQUERIES, partial(botproperties.toggle_value, 'inlinequeries')))
    add(ActionHandler(Actions.EDIT_BOT_OFFICIAL, partial(botproperties.toggle_value, 'official')))
    add(ActionHandler(Actions.EDIT_BOT_OFFLINE, partial(botproperties.toggle_value, 'offline')))
    add(ActionHandler(Actions.EDIT_BOT_SPAM, partial(botproperties.toggle_value, 'spam')))
    add(ActionHandler(Actions.CONFIRM_DELETE_BOT, botproperties.delete_bot_confirm))
    add(ActionHandler(Actions.DELETE_BOT, botproperties.delete_bot))
    add(ActionHandler(Actions.ACCEPT_SUGGESTION, botproperties.accept_suggestion))
    add(ActionHandler(Actions.REJECT_SUGGESTION, botproperties.reject_suggestion))
    add(ActionHandler(Actions.CHANGE_SUGGESTION, botproperties.change_suggestion))
    add(ActionHandler(Actions.SWITCH_SUGGESTIONS_PAGE, admin.approve_suggestions))
    add(ActionHandler(Actions.SWITCH_APPROVALS_PAGE, admin.approve_bots))
    add(ActionHandler(Actions.SET_NOTIFICATIONS, set_notifications))
    add(ActionHandler(Actions.SEND_NEW_BOTS, send_new_bots))
    add(ActionHandler(Actions.SET_KEYWORDS, botproperties.set_keywords))
    add(ActionHandler(Actions.ABORT_SETTING_KEYWORDS, admin.edit_bot))
    add(ActionHandler(Actions.SEND_BOTLIST, botlist.send_botlist))
    add(ActionHandler(Actions.RESEND_BOTLIST, partial(botlist.send_botlist, resent=True)))
    add(ActionHandler(Actions.SEND_BROADCAST, broadcasts.send_broadcast))
    add(ActionHandler(Actions.PIN_MESSAGE, broadcasts.pin_message))
    add(ActionHandler(Actions.ADD_THANK_YOU, basic.add_thank_you_button))
    add(ActionHandler(Actions.EXPLORE, explore.explore))

    keywords_handler = ConversationHandler(
        entry_points=[
            ActionHandler(Actions.EDIT_BOT_KEYWORDS, botproperties.set_keywords_init)
        ],
        states={
            BotStates.SENDING_KEYWORDS: [
                MessageHandler(Filters.text, botproperties.add_keyword),
                ActionHandler(Actions.REMOVE_KEYWORD, botproperties.remove_keyword),
                ActionHandler(Actions.DELETE_KEYWORD_SUGGESTION, botproperties.delete_keyword_suggestion),
            ],
        },
        fallbacks=[
            # TODO
        ],
        per_user=True,
        allow_reentry=False
    )
    add(keywords_handler)

    broadcasting_handler = ConversationHandler(
        entry_points=[
            ActionHandler(Actions.SEND_BROADCAST, broadcasts.broadcast),
        ],
        states={
            BotStates.BROADCASTING: [
                MessageHandler(Filters.text, broadcasts.broadcast_preview),
            ],
        },
        fallbacks=[],
        per_user=True,
        per_chat=False,
        allow_reentry=True
    )
    add(broadcasting_handler)

    add(ActionHandler(Actions.ADD_TO_FAVORITES, favorites.add_favorite))

    add(CommandHandler(('cat', 'category', 'categories'), select_category))
    add(CommandHandler(('s', 'search'), search_handler))

    add(MessageHandler(Filters.reply, reply_router), group=-1)
    add(MessageHandler(Filters.forwarded, forward_router))

    add(CommandHandler("admin", admin.menu))
    add(CommandHandler("a", admin.menu))

    add(CommandHandler(
        ('rej', 'reject'),
        admin.reject_bot_submission))
    add(CommandHandler(('rejsil', 'rejectsil', 'rejsilent', 'rejectsilent'),
                       lambda bot, update: admin.reject_bot_submission(
                           bot, update, None, notify_submittant=False)))

    # admin menu
    # add(RegexHandler(captions.APPROVE_BOTS + '.*', admin.approve_bots))
    # add(RegexHandler(captions.APPROVE_SUGGESTIONS + '.*', admin.approve_suggestions))
    # add(RegexHandler(captions.PENDING_UPDATE + '.*', admin.pending_update))
    # add(RegexHandler(captions.SEND_BOTLIST, admin.prepare_transmission))
    # add(RegexHandler(captions.FIND_OFFLINE, admin.send_offline))
    # add(RegexHandler(captions.SEND_CONFIG_FILES, admin.send_runtime_files))
    # add(RegexHandler(captions.SEND_ACTIVITY_LOGS, admin.send_activity_logs))

    # main menu
    # add(RegexHandler(captions.ADMIN_MENU, admin.menu))
    # add(RegexHandler(captions.REFRESH, admin.menu))
    # add(RegexHandler(captions.CATEGORIES, select_category))
    # add(RegexHandler(captions.FAVORITES, favorites.send_favorites_list))
    # add(RegexHandler(captions.NEW_BOTS, send_new_bots))
    # add(RegexHandler(captions.SEARCH, search_handler))
    # add(RegexHandler(captions.CONTRIBUTING, help.contributing))
    # add(RegexHandler(captions.EXAMPLES, help.examples))
    # add(RegexHandler(captions.HELP, help.help))

    add(RegexHandler("^/edit\d+$", admin.edit_bot), group=1)

    add(RegexHandler("^/approve\d+$", admin.edit_bot), group=1)
    add(CommandHandler('approve', admin.short_approve_list))

    add(CommandHandler(('manybot', 'manybots'), admin.manybots))

    add(CommandHandler('new', partial(contributions.new_bot_submission, bot_checker=bot_checker)))
    add(RegexHandler('.*#new.*', partial(contributions.new_bot_submission, bot_checker=bot_checker)), group=1)
    add(CommandHandler('offline', contributions.notify_bot_offline))
    add(RegexHandler('.*#offline.*', contributions.notify_bot_offline), group=1)
    add(CommandHandler('spam', contributions.notify_bot_spammy))
    add(RegexHandler('.*#spam.*', contributions.notify_bot_spammy), group=1)

    add(CommandHandler('help', help.help))
    add(CommandHandler(("contribute", "contributing"), help.contributing))
    add(CommandHandler("examples", help.examples))
    add(CommandHandler("rules", help.rules))

    add(CommandHandler(("addfav", "addfavorite"), favorites.add_favorite_handler))
    add(CommandHandler(("f", "fav", "favorites"), favorites.send_favorites_list))

    add(CommandHandler("official", explore.show_official))

    add(CommandHandler('ban', partial(admin.ban_handler, ban_state=True)))
    add(CommandHandler('unban', partial(admin.ban_handler, ban_state=False)))
    add(CommandHandler('t3chno', t3chnostats))
    add(CommandHandler('random', eastereggs.send_random_bot))
    add(CommandHandler('easteregg', eastereggs.send_next))

    add(CommandHandler("subscribe", manage_subscription))
    add(CommandHandler("newbots", send_new_bots))

    add(CommandHandler("accesstoken", access_token))

    add(CommandHandler(('stat', 'stats', 'statistic', 'statistics'), admin.send_statistic))

    add(CommandHandler(('log', 'logs'), admin.send_activity_logs))
    add(CommandHandler(
        ('debug', 'analysis', 'ana', 'analyze'),
        lambda bot, update, args: admin.send_activity_logs(bot, update, args, Statistic.ANALYSIS),
        pass_args=True))
    add(CommandHandler(
        'info',
        lambda bot, update, args: admin.send_activity_logs(bot, update, args, Statistic.INFO),
        pass_args=True))
    add(CommandHandler(('detail', 'detailed'),
                       lambda bot, update, args: admin.send_activity_logs(bot, update, args,
                                                                          Statistic.DETAILED),
                       pass_args=True))
    add(CommandHandler(
        ('warn', 'warning'),
        lambda bot, update, args: admin.send_activity_logs(bot, update, args, Statistic.WARN),
        pass_args=True))
    add(CommandHandler(
        'important',
        lambda bot, update, args: admin.send_activity_logs(bot, update, args, Statistic.IMPORTANT),
        pass_args=True))

    add(MessageHandler(
        Filters.text,
        lambda bot, update: botlistchat.text_message_logger(bot, update, log)
    ), group=99)

    for hashtag in HINTS.keys():
        add(RegexHandler(r'{}.*'.format(hashtag), botlistchat.hint_handler), group=1)
    add(CommandHandler(('hint', 'hints'), botlistchat.show_available_hints))

    add(CommandHandler('ping', basic.ping))
    add(RegexHandler('^{}$'.format(settings.REGEX_BOT_ONLY), send_bot_details,
                     pass_chat_data=True))

    add(ChosenInlineActionHandler(Actions.DELETE_INLINE_RESULT, components.basic.delete_chosen_inline_result))
    add(InlineQueryActionHandler(Actions.EDIT_BOT, admin.edit_bot))

    add(InlineQueryHandler(inlinequeries.inlinequery_handler))
    add(MessageHandler(Filters.all, all_handler), group=98)
