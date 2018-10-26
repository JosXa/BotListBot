import json
import re
import traceback
from functools import partial
from logzero import logger as log

from telegram.ext import CallbackQueryHandler, ChosenInlineResultHandler, CommandHandler, \
    ConversationHandler, Dispatcher, DispatcherHandlerStop, Filters, InlineQueryHandler, \
    MessageHandler, RegexHandler

import captions
import components.botproperties
import settings
import util
from components import admin, basic, botlist, botlistchat, botproperties, broadcasts, \
    contributions, eastereggs, \
    explore, favorites, help, inlinequeries
from components.basic import all_handler
from components.botlistchat import HINTS
from components.explore import select_category, send_bot_details, send_category, show_new_bots
from components.misc import access_token, set_notifications, t3chnostats
from components.search import search_handler, search_query
from const import BotStates, CallbackActions
from dialog import messages
from lib import InlineCallbackHandler
from misc import manage_subscription
from models import Bot, Category, Country, Favorite, Keyword, Statistic, Suggestion, User

try:
    from components.userbot import BotChecker
except:
    pass


def callback_router(bot, update, chat_data, user_data, job_queue):
    obj = json.loads(str(update.callback_query.data))
    user = User.from_update(update)

    try:
        if 'a' in obj:
            action = obj['a']

            # BOTLISTCHAT
            if action == CallbackActions.DELETE_CONVERSATION:
                botlistchat.delete_conversation(bot, update, chat_data)
            # HELP
            elif action == CallbackActions.HELP:
                help.help(bot, update)
            elif action == CallbackActions.CONTRIBUTING:
                help.contributing(bot, update)
            elif action == CallbackActions.EXAMPLES:
                help.examples(bot, update)
            # BASIC QUERYING
            elif action == CallbackActions.SELECT_CATEGORY:
                select_category(bot, update, chat_data)
            elif action == CallbackActions.SELECT_BOT_FROM_CATEGORY:
                category = Category.get(id=obj['id'])
                send_category(bot, update, chat_data, category)
            elif action == CallbackActions.SEND_BOT_DETAILS:
                item = Bot.get(id=obj['id'])
                send_bot_details(bot, update, chat_data, item)
            # FAVORITES
            elif action == CallbackActions.TOGGLE_FAVORITES_LAYOUT:
                value = obj['v']
                favorites.toggle_favorites_layout(bot, update, value)
            elif action == CallbackActions.ADD_FAVORITE:
                favorites.add_favorite_handler(bot, update)
            elif action == CallbackActions.REMOVE_FAVORITE_MENU:
                favorites.remove_favorite_menu(bot, update)
            elif action == CallbackActions.REMOVE_FAVORITE:
                to_remove = Favorite.get(id=obj['id'])
                bot_details = to_remove.bot
                to_remove.delete_instance()
                if obj.get('details'):
                    send_bot_details(bot, update, chat_data, bot_details)
                else:
                    favorites.remove_favorite_menu(bot, update)
            elif action == CallbackActions.SEND_FAVORITES_LIST:
                favorites.send_favorites_list(bot, update)
            elif action == CallbackActions.ADD_ANYWAY:
                favorites.add_custom(bot, update, obj['u'])
            elif action == CallbackActions.ADD_TO_FAVORITES:
                details = obj.get('details')
                discreet = obj.get('discreet', False) or details
                item = Bot.get(id=obj['id'])
                favorites.add_favorite(bot, update, item, callback_alert=discreet)
                if details:
                    send_bot_details(bot, update, chat_data, item)
            # ACCEPT/REJECT BOT SUBMISSIONS
            elif action == CallbackActions.APPROVE_REJECT_BOTS:
                custom_approve_list = [Bot.get(id=obj['id'])]
                admin.approve_bots(bot, update, override_list=custom_approve_list)
            elif action == CallbackActions.ACCEPT_BOT:
                to_accept = Bot.get(id=obj['id'])
                admin.edit_bot_category(bot, update, to_accept, CallbackActions.BOT_ACCEPTED)
                # Run in x minutes, giving the moderator enough time to edit bot details
                job_queue.run_once(lambda b, job:
                                   botlistchat.notify_group_submission_accepted(b, job, to_accept),
                                   settings.BOT_ACCEPTED_IDLE_TIME * 60)
            elif action == CallbackActions.RECOMMEND_MODERATOR:
                bot_in_question = Bot.get(id=obj['id'])
                admin.recommend_moderator(bot, update, bot_in_question, obj['page'])
            elif action == CallbackActions.SELECT_MODERATOR:
                bot_in_question = Bot.get(id=obj['bot_id'])
                moderator = User.get(id=obj['uid'])
                admin.share_with_moderator(bot, update, bot_in_question, moderator)
                admin.approve_bots(bot, update, obj['page'])
            elif action == CallbackActions.REJECT_BOT:
                to_reject = Bot.get(id=obj['id'])
                notification = obj.get('ntfc', True)
                admin.reject_bot_submission(bot, update, None, to_reject, verbose=False,
                                            notify_submittant=notification)
                admin.approve_bots(bot, update, obj['page'])
            elif action == CallbackActions.BOT_ACCEPTED:
                to_accept = Bot.get(id=obj['bid'])
                category = Category.get(id=obj['cid'])
                admin.accept_bot_submission(bot, update, to_accept, category)
            elif action == CallbackActions.COUNT_THANK_YOU:
                new_count = obj.get('count', 1)
                basic.count_thank_you(bot, update, new_count)
            # ADD BOT
            # elif action == CallbackActions.ADD_BOT_SELECT_CAT:
            #     category = Category.get(id=obj['id'])
            #     admin.add_bot(bot, update, chat_data, category)
            # EDIT BOT
            elif action == CallbackActions.EDIT_BOT:
                to_edit = Bot.get(id=obj['id'])
                admin.edit_bot(bot, update, chat_data, to_edit)
            elif action == CallbackActions.EDIT_BOT_SELECT_CAT:
                to_edit = Bot.get(id=obj['id'])
                admin.edit_bot_category(bot, update, to_edit)
            elif action == CallbackActions.EDIT_BOT_CAT_SELECTED:
                to_edit = Bot.get(id=obj['bid'])
                cat = Category.get(id=obj['cid'])
                botproperties.change_category(bot, update, to_edit, cat)
                admin.edit_bot(bot, update, chat_data, to_edit)
            elif action == CallbackActions.EDIT_BOT_COUNTRY:
                to_edit = Bot.get(id=obj['id'])
                botproperties.set_country_menu(bot, update, to_edit)
            elif action == CallbackActions.SET_COUNTRY:
                to_edit = Bot.get(id=obj['bid'])
                if obj['cid'] == 'None':
                    country = None
                else:
                    country = Country.get(id=obj['cid'])
                botproperties.set_country(bot, update, to_edit, country)
                admin.edit_bot(bot, update, chat_data, to_edit)
            elif action == CallbackActions.EDIT_BOT_DESCRIPTION:
                to_edit = Bot.get(id=obj['id'])
                botproperties.set_text_property(bot, update, chat_data, 'description', to_edit)
            elif action == CallbackActions.EDIT_BOT_EXTRA:
                to_edit = Bot.get(id=obj['id'])
                # SAME IS DONE HERE, but manually
                botproperties.set_text_property(bot, update, chat_data, 'extra', to_edit)
            elif action == CallbackActions.EDIT_BOT_NAME:
                to_edit = Bot.get(id=obj['id'])
                botproperties.set_text_property(bot, update, chat_data, 'name', to_edit)
            elif action == CallbackActions.EDIT_BOT_USERNAME:
                to_edit = Bot.get(id=obj['id'])
                botproperties.set_text_property(bot, update, chat_data, 'username', to_edit)
            # elif action == CallbackActions.EDIT_BOT_KEYWORDS:
            #     to_edit = Bot.get(id=obj['id'])
            #     botproperties.set_keywords_init(bot, update, chat_data, to_edit)
            elif action == CallbackActions.APPLY_ALL_CHANGES:
                to_edit = Bot.get(id=obj['id'])
                admin.apply_all_changes(bot, update, chat_data, to_edit)
            elif action == CallbackActions.EDIT_BOT_INLINEQUERIES:
                to_edit = Bot.get(id=obj['id'])
                value = bool(obj['value'])
                botproperties.toggle_value(bot, update, 'inlinequeries', to_edit, value)
                admin.edit_bot(bot, update, chat_data, to_edit)
            elif action == CallbackActions.EDIT_BOT_OFFICIAL:
                to_edit = Bot.get(id=obj['id'])
                value = bool(obj['value'])
                botproperties.toggle_value(bot, update, 'official', to_edit, value)
                admin.edit_bot(bot, update, chat_data, to_edit)
            elif action == CallbackActions.EDIT_BOT_OFFLINE:
                to_edit = Bot.get(id=obj['id'])
                value = bool(obj['value'])
                botproperties.toggle_value(bot, update, 'offline', to_edit, value)
                admin.edit_bot(bot, update, chat_data, to_edit)
            elif action == CallbackActions.EDIT_BOT_SPAM:
                to_edit = Bot.get(id=obj['id'])
                value = bool(obj['value'])
                botproperties.toggle_value(bot, update, 'spam', to_edit, value)
                admin.edit_bot(bot, update, chat_data, to_edit)
            elif action == CallbackActions.CONFIRM_DELETE_BOT:
                to_delete = Bot.get(id=obj['id'])
                botproperties.delete_bot_confirm(bot, update, to_delete)
            elif action == CallbackActions.DELETE_BOT:
                to_edit = Bot.get(id=obj['id'])
                botproperties.delete_bot(bot, update, to_edit)
                # send_category(bot, update, chat_data, to_edit.category)
            elif action == CallbackActions.ACCEPT_SUGGESTION:
                suggestion = Suggestion.get(id=obj['id'])
                components.botproperties.accept_suggestion(bot, update, suggestion)
                admin.approve_suggestions(bot, update, page=obj['page'])
            elif action == CallbackActions.REJECT_SUGGESTION:
                suggestion = Suggestion.get(id=obj['id'])
                suggestion.delete_instance()
                admin.approve_suggestions(bot, update, page=obj['page'])
            elif action == CallbackActions.CHANGE_SUGGESTION:
                suggestion = Suggestion.get(id=obj['id'])
                botproperties.change_suggestion(bot, update, suggestion, page_handover=obj['page'])
            elif action == CallbackActions.SWITCH_SUGGESTIONS_PAGE:
                page = obj['page']
                admin.approve_suggestions(bot, update, page)
            elif action == CallbackActions.SWITCH_APPROVALS_PAGE:
                admin.approve_bots(bot, update, page=obj['page'])
            elif action == CallbackActions.SET_NOTIFICATIONS:
                set_notifications(bot, update, obj['value'])
            elif action == CallbackActions.NEW_BOTS_SELECTED:
                show_new_bots(bot, update, chat_data, back_button=True)
            elif action == CallbackActions.ABORT_SETTING_KEYWORDS:
                to_edit = Bot.get(id=obj['id'])
                admin.edit_bot(bot, update, chat_data, to_edit)
            # SENDING BOTLIST
            elif action == CallbackActions.SEND_BOTLIST:
                silent = obj.get('silent', False)
                re_send = obj.get('re', False)
                botlist.send_botlist(bot, update, resend=re_send, silent=silent)
            elif action == CallbackActions.RESEND_BOTLIST:
                botlist.send_botlist(bot, update, resend=True)
            # BROADCASTING
            elif action == 'send_broadcast':
                broadcasts.send_broadcast(bot, update, user_data)
            elif action == 'pin_message':
                broadcasts.pin_message(bot, update, obj['mid'])
            elif action == 'add_thank_you':
                basic.add_thank_you_button(bot, update, obj['cid'], obj['mid'])
            # EXPLORING
            elif action == CallbackActions.EXPLORE_NEXT:
                explore.explore(bot, update, chat_data)
    except Exception as e:
        traceback.print_exc()

        # get the callback action in plaintext
        actions = dict(CallbackActions.__dict__)
        a = next(k for k, v in actions.items() if v == obj.get('a'))
        util.send_md_message(bot, settings.ADMINS[0],
                             "Exception in callback query for {}:\n{}\n\nWith CallbackAction {}\n\nWith data:\n{}".format(
                                 user.markdown_short,
                                 util.escape_markdown(e),
                                 util.escape_markdown(a),
                                 util.escape_markdown(str(obj))
                             ))
    finally:
        bot.answerCallbackQuery(update.callback_query.id)
        return ConversationHandler.END


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


def reply_router(bot, update, chat_data):
    text = update.effective_message.reply_to_message.text

    if text == messages.ADD_FAVORITE:
        query = update.message.text
        favorites.add_favorite_handler(bot, update, query)
    elif text == messages.SEARCH_MESSAGE:
        query = update.message.text
        search_query(bot, update, chat_data, query)

    # BOTPROPERTIES
    bot_properties = ['description', 'extra', 'name', 'username']
    try:
        partition = text.partition(messages.BOTPROPERTY_STARTSWITH)
    except AttributeError:
        return
    if partition[1] != '':
        bot_property = next(p for p in bot_properties if partition[2].startswith(p))
        # Reply for setting a bot property
        botproperties.set_text_property(bot, update, chat_data, bot_property)
        print('raising...')
        print(partition)
        print(partition[1])
        raise DispatcherHandlerStop
    elif text == messages.BAN_MESSAGE:
        query = update.message.text
        admin.ban_handler(bot, update, query, chat_data, True)
    elif text == messages.UNBAN_MESSAGE:
        query = update.message.text
        admin.ban_handler(bot, update, query, chat_data, False)


def register(dp: Dispatcher, bot_checker: 'BotChecker'):
    def add(*args, **kwargs):
        dp.add_handler(*args, **kwargs)

    keywords_handler = ConversationHandler(
        entry_points=[
            InlineCallbackHandler(CallbackActions.EDIT_BOT_KEYWORDS,
                                  botproperties.set_keywords_init,
                                  serialize=lambda data: dict(to_edit=Bot.get(id=data['id'])),
                                  pass_chat_data=True)
        ],
        states={
            BotStates.SENDING_KEYWORDS: [
                MessageHandler(Filters.text, botproperties.add_keyword, pass_chat_data=True),
                InlineCallbackHandler(CallbackActions.REMOVE_KEYWORD,
                                      botproperties.remove_keyword,
                                      serialize=lambda data: dict(
                                          to_edit=Bot.get(id=data['id']),
                                          keyword=Keyword.get(id=data['kwid'])
                                      ),
                                      pass_chat_data=True),
                InlineCallbackHandler(CallbackActions.DELETE_KEYWORD_SUGGESTION,
                                      botproperties.delete_keyword_suggestion,
                                      serialize=lambda data: dict(
                                          to_edit=Bot.get(id=data['id']),
                                          suggestion=Suggestion.get(id=data['suggid'])
                                      ),
                                      pass_chat_data=True)
            ],
        },
        fallbacks=[
            CallbackQueryHandler(callback_router, pass_chat_data=True, pass_user_data=True,
                                 pass_job_queue=True)
        ],
        per_user=True,
        allow_reentry=False

    )
    add(keywords_handler)

    broadcasting_handler = ConversationHandler(
        entry_points=[
            InlineCallbackHandler('broadcast', broadcasts.broadcast, pass_user_data=True),
            CommandHandler("broadcast", broadcasts.broadcast, pass_user_data=True),
            CommandHandler("bc", broadcasts.broadcast, pass_user_data=True)
        ],
        states={
            BotStates.BROADCASTING: [
                MessageHandler(Filters.text, broadcasts.broadcast_preview, pass_user_data=True),
            ],
        },
        fallbacks=[],
        per_user=True,
        per_chat=False,
        allow_reentry=True
    )
    add(broadcasting_handler)

    add(CallbackQueryHandler(callback_router, pass_chat_data=True, pass_user_data=True,
                             pass_job_queue=True))

    add(CommandHandler(('cat', 'category', 'categories'), select_category, pass_chat_data=True))
    add(CommandHandler(('s', 'search'), search_handler, pass_args=True, pass_chat_data=True))

    add(MessageHandler(Filters.reply, reply_router, pass_chat_data=True), group=-1)
    add(MessageHandler(Filters.forwarded, forward_router, pass_chat_data=True))

    add(CommandHandler("admin", admin.menu))
    add(CommandHandler("a", admin.menu))

    add(CommandHandler(
        ('rej', 'reject'),
        admin.reject_bot_submission, pass_args=True))
    add(CommandHandler(('rejsil', 'rejectsil', 'rejsilent', 'rejectsilent'),
                       lambda bot, update: admin.reject_bot_submission(
                           bot, update, None, notify_submittant=False)))

    # admin menu
    add(RegexHandler(captions.APPROVE_BOTS + '.*', admin.approve_bots))
    add(RegexHandler(captions.APPROVE_SUGGESTIONS + '.*', admin.approve_suggestions))
    add(RegexHandler(captions.PENDING_UPDATE + '.*', admin.pending_update))
    add(RegexHandler(captions.SEND_BOTLIST, admin.prepare_transmission, pass_chat_data=True))
    add(RegexHandler(captions.FIND_OFFLINE, admin.send_offline))
    add(RegexHandler(captions.SEND_CONFIG_FILES, admin.send_runtime_files))
    add(RegexHandler(captions.SEND_ACTIVITY_LOGS, admin.send_activity_logs))

    # main menu
    add(RegexHandler(captions.ADMIN_MENU, admin.menu))
    add(RegexHandler(captions.REFRESH, admin.menu))
    add(RegexHandler(captions.CATEGORIES, select_category, pass_chat_data=True))
    add(RegexHandler(captions.EXPLORE, explore.explore, pass_chat_data=True))
    add(RegexHandler(captions.FAVORITES, favorites.send_favorites_list))
    add(RegexHandler(captions.NEW_BOTS, show_new_bots, pass_chat_data=True))
    add(RegexHandler(captions.SEARCH, search_handler, pass_chat_data=True))
    add(RegexHandler(captions.CONTRIBUTING, help.contributing))
    add(RegexHandler(captions.EXAMPLES, help.examples))
    add(RegexHandler(captions.HELP, help.help))

    add(RegexHandler("^/edit\d+$", admin.edit_bot, pass_chat_data=True), group=1)

    add(RegexHandler("^/approve\d+$", admin.edit_bot, pass_chat_data=True), group=1)
    add(CommandHandler('approve', admin.short_approve_list))

    add(CommandHandler(('manybot', 'manybots'), admin.manybots))

    add(
        CommandHandler(
            'new',
            partial(contributions.new_bot_submission, bot_checker=bot_checker),
            pass_args=True,
            pass_chat_data=True
        ))
    add(
        RegexHandler(
            '.*#new.*',
            lambda bot, update, chat_data: contributions.new_bot_submission(
                bot, update, chat_data, args=None, bot_checker=bot_checker),
            pass_chat_data=True),
        group=1
    )
    add(CommandHandler('offline', contributions.notify_bot_offline, pass_args=True))
    add(RegexHandler('.*#offline.*', contributions.notify_bot_offline), group=1)
    add(CommandHandler('spam', contributions.notify_bot_spam, pass_args=True))
    add(RegexHandler('.*#spam.*', contributions.notify_bot_spam), group=1)

    add(CommandHandler('help', help.help))
    add(CommandHandler(("contribute", "contributing"), help.contributing))
    add(CommandHandler("examples", help.examples))
    add(CommandHandler("rules", help.rules))

    add(CommandHandler(("addfav", "addfavorite"), favorites.add_favorite_handler, pass_args=True))
    add(CommandHandler(("f", "fav", "favorites"), favorites.send_favorites_list))

    add(CommandHandler(("e", "explore"), explore.explore, pass_chat_data=True))
    add(CommandHandler("official", explore.show_official))

    add(CommandHandler('ban', partial(admin.ban_handler, ban_state=True), pass_args=True,
                       pass_chat_data=True))
    add(CommandHandler('unban', partial(admin.ban_handler, ban_state=False), pass_args=True,
                       pass_chat_data=True))
    add(CommandHandler('t3chno', t3chnostats))
    add(CommandHandler('random', eastereggs.send_random_bot))
    add(CommandHandler('easteregg', eastereggs.send_next, pass_args=True))

    add(CommandHandler("subscribe", manage_subscription))
    add(CommandHandler("newbots", show_new_bots, pass_chat_data=True))

    add(CommandHandler("accesstoken", access_token))

    add(CommandHandler(('stat', 'stats', 'statistic', 'statistics'), admin.send_statistic))

    add(CommandHandler(('log', 'logs'), admin.send_activity_logs, pass_args=True))
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

    add(ChosenInlineResultHandler(inlinequeries.chosen_result, pass_chat_data=True))
    add(InlineQueryHandler(inlinequeries.inlinequery_handler, pass_chat_data=True))
    add(MessageHandler(Filters.all, all_handler, pass_chat_data=True), group=98)
